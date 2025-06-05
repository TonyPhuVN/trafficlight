"""
🎯 Traffic Scenario Manager
Manages the lifecycle of traffic processing scenarios with proper resource cleanup
"""

import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
import gc

class ScenarioStatus(Enum):
    """Status of a traffic scenario"""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CLEANUP = "cleanup"
    CLOSED = "closed"

@dataclass
class TrafficScenario:
    """Represents a traffic processing scenario"""
    id: str
    intersection_id: str
    status: ScenarioStatus = ScenarioStatus.CREATED
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    
    # Processing data
    vehicles_processed: int = 0
    predictions_made: int = 0
    light_changes: int = 0
    errors: List[str] = field(default_factory=list)
    
    # Resource tracking
    allocated_resources: Dict[str, Any] = field(default_factory=dict)
    cleanup_callbacks: List[callable] = field(default_factory=list)
    
    # Performance metrics
    processing_time: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0

class ScenarioManager:
    """Manages traffic processing scenarios with proper lifecycle and cleanup"""
    
    def __init__(self, max_concurrent_scenarios: int = 10, 
                 scenario_timeout: int = 300):
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.max_concurrent_scenarios = max_concurrent_scenarios
        self.scenario_timeout = scenario_timeout
        
        # Active scenarios tracking
        self.active_scenarios: Dict[str, TrafficScenario] = {}
        self.completed_scenarios: List[TrafficScenario] = []
        
        # Threading
        self.lock = threading.RLock()
        self.cleanup_thread = None
        self.running = False
        
        # Statistics
        self.total_scenarios_created = 0
        self.total_scenarios_completed = 0
        self.total_scenarios_failed = 0
        self.total_cleanup_operations = 0
        
        self.logger.info("🎯 Scenario Manager initialized")
    
    def start(self):
        """Start the scenario manager"""
        if self.running:
            return
        
        self.running = True
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
            name="ScenarioCleanup"
        )
        self.cleanup_thread.start()
        
        self.logger.info("🚀 Scenario Manager started")
    
    def stop(self):
        """Stop the scenario manager and cleanup all scenarios"""
        self.running = False
        
        # Close all active scenarios
        with self.lock:
            active_ids = list(self.active_scenarios.keys())
        
        for scenario_id in active_ids:
            self.close_scenario(scenario_id, force=True)
        
        # Wait for cleanup thread
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=10)
        
        self.logger.info("🛑 Scenario Manager stopped")
    
    def create_scenario(self, intersection_id: str, 
                       processing_params: Dict[str, Any] = None) -> str:
        """Create a new traffic processing scenario"""
        
        with self.lock:
            # Check if we're at capacity
            if len(self.active_scenarios) >= self.max_concurrent_scenarios:
                self._force_cleanup_oldest()
            
            # Generate unique scenario ID
            scenario_id = f"scenario_{intersection_id}_{uuid.uuid4().hex[:8]}"
            
            # Create scenario
            scenario = TrafficScenario(
                id=scenario_id,
                intersection_id=intersection_id
            )
            
            # Initialize processing parameters
            if processing_params:
                scenario.allocated_resources.update(processing_params)
            
            # Track scenario
            self.active_scenarios[scenario_id] = scenario
            self.total_scenarios_created += 1
            
            self.logger.info(f"🎯 Created scenario {scenario_id} for {intersection_id}")
            
            return scenario_id
    
    def start_scenario(self, scenario_id: str) -> bool:
        """Start processing a scenario"""
        with self.lock:
            scenario = self.active_scenarios.get(scenario_id)
            if not scenario:
                self.logger.error(f"❌ Scenario {scenario_id} not found")
                return False
            
            if scenario.status != ScenarioStatus.CREATED:
                self.logger.warning(f"⚠️ Scenario {scenario_id} already started")
                return False
            
            # Update scenario status
            scenario.status = ScenarioStatus.RUNNING
            scenario.started_at = datetime.now()
            
            self.logger.info(f"🚀 Started scenario {scenario_id}")
            return True
    
    def update_scenario_progress(self, scenario_id: str,
                               vehicles_processed: int = 0,
                               predictions_made: int = 0,
                               light_changes: int = 0,
                               processing_time: float = 0.0,
                               error: str = None):
        """Update scenario progress and metrics"""
        with self.lock:
            scenario = self.active_scenarios.get(scenario_id)
            if not scenario:
                return False
            
            # Update counters
            scenario.vehicles_processed += vehicles_processed
            scenario.predictions_made += predictions_made
            scenario.light_changes += light_changes
            scenario.processing_time += processing_time
            
            # Track errors
            if error:
                scenario.errors.append(f"{datetime.now().isoformat()}: {error}")
            
            # Update performance metrics
            scenario.memory_usage = self._get_memory_usage()
            
            return True
    
    def complete_scenario(self, scenario_id: str, success: bool = True) -> bool:
        """Mark a scenario as completed"""
        with self.lock:
            scenario = self.active_scenarios.get(scenario_id)
            if not scenario:
                self.logger.error(f"❌ Scenario {scenario_id} not found")
                return False
            
            # Update scenario status
            scenario.status = ScenarioStatus.COMPLETED if success else ScenarioStatus.FAILED
            scenario.completed_at = datetime.now()
            
            if scenario.started_at:
                scenario.duration_seconds = (scenario.completed_at - scenario.started_at).total_seconds()
            
            # Update statistics
            if success:
                self.total_scenarios_completed += 1
            else:
                self.total_scenarios_failed += 1
            
            self.logger.info(f"✅ Completed scenario {scenario_id} in {scenario.duration_seconds:.2f}s")
            
            # Schedule for cleanup
            scenario.status = ScenarioStatus.CLEANUP
            
            return True
    
    def close_scenario(self, scenario_id: str, force: bool = False) -> bool:
        """Close and cleanup a scenario"""
        with self.lock:
            scenario = self.active_scenarios.get(scenario_id)
            if not scenario:
                return False
            
            self.logger.info(f"🧹 Closing scenario {scenario_id}")
            
            try:
                # Run cleanup callbacks
                for cleanup_callback in scenario.cleanup_callbacks:
                    try:
                        cleanup_callback()
                    except Exception as e:
                        self.logger.error(f"❌ Cleanup callback error: {e}")
                
                # Clear allocated resources
                for resource_name, resource in scenario.allocated_resources.items():
                    try:
                        if hasattr(resource, 'close'):
                            resource.close()
                        elif hasattr(resource, 'cleanup'):
                            resource.cleanup()
                        elif hasattr(resource, 'release'):
                            resource.release()
                    except Exception as e:
                        self.logger.error(f"❌ Resource cleanup error for {resource_name}: {e}")
                
                # Clear resource references
                scenario.allocated_resources.clear()
                scenario.cleanup_callbacks.clear()
                
                # Update status
                scenario.status = ScenarioStatus.CLOSED
                
                # Move to completed scenarios
                self.completed_scenarios.append(scenario)
                del self.active_scenarios[scenario_id]
                
                # Limit completed scenarios history
                if len(self.completed_scenarios) > 100:
                    self.completed_scenarios = self.completed_scenarios[-50:]
                
                self.total_cleanup_operations += 1
                
                # Force garbage collection
                gc.collect()
                
                self.logger.info(f"✅ Scenario {scenario_id} closed successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"❌ Error closing scenario {scenario_id}: {e}")
                scenario.status = ScenarioStatus.FAILED
                scenario.errors.append(f"Cleanup error: {str(e)}")
                return False
    
    def add_resource_to_scenario(self, scenario_id: str, 
                               resource_name: str, resource: Any,
                               cleanup_callback: callable = None) -> bool:
        """Add a resource to a scenario for tracking and cleanup"""
        with self.lock:
            scenario = self.active_scenarios.get(scenario_id)
            if not scenario:
                return False
            
            scenario.allocated_resources[resource_name] = resource
            
            if cleanup_callback:
                scenario.cleanup_callbacks.append(cleanup_callback)
            
            return True
    
    def get_scenario_status(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Get scenario status and metrics"""
        with self.lock:
            scenario = self.active_scenarios.get(scenario_id)
            if not scenario:
                # Check completed scenarios
                for completed in self.completed_scenarios:
                    if completed.id == scenario_id:
                        scenario = completed
                        break
                
                if not scenario:
                    return None
            
            return {
                'id': scenario.id,
                'intersection_id': scenario.intersection_id,
                'status': scenario.status.value,
                'created_at': scenario.created_at.isoformat(),
                'started_at': scenario.started_at.isoformat() if scenario.started_at else None,
                'completed_at': scenario.completed_at.isoformat() if scenario.completed_at else None,
                'duration_seconds': scenario.duration_seconds,
                'vehicles_processed': scenario.vehicles_processed,
                'predictions_made': scenario.predictions_made,
                'light_changes': scenario.light_changes,
                'errors': scenario.errors,
                'allocated_resources': list(scenario.allocated_resources.keys()),
                'processing_time': scenario.processing_time,
                'memory_usage': scenario.memory_usage
            }
    
    def get_active_scenarios(self) -> List[Dict[str, Any]]:
        """Get all active scenarios"""
        with self.lock:
            return [self.get_scenario_status(sid) for sid in self.active_scenarios.keys()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scenario manager statistics"""
        with self.lock:
            return {
                'total_scenarios_created': self.total_scenarios_created,
                'total_scenarios_completed': self.total_scenarios_completed,
                'total_scenarios_failed': self.total_scenarios_failed,
                'total_cleanup_operations': self.total_cleanup_operations,
                'active_scenarios_count': len(self.active_scenarios),
                'completed_scenarios_count': len(self.completed_scenarios),
                'max_concurrent_scenarios': self.max_concurrent_scenarios,
                'scenario_timeout': self.scenario_timeout
            }
    
    def _cleanup_loop(self):
        """Background cleanup loop"""
        while self.running:
            try:
                self._cleanup_expired_scenarios()
                self._cleanup_completed_scenarios()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                self.logger.error(f"❌ Cleanup loop error: {e}")
                time.sleep(60)
    
    def _cleanup_expired_scenarios(self):
        """Cleanup scenarios that have exceeded timeout"""
        now = datetime.now()
        expired_scenarios = []
        
        with self.lock:
            for scenario_id, scenario in self.active_scenarios.items():
                if scenario.status == ScenarioStatus.RUNNING:
                    if scenario.started_at:
                        elapsed = (now - scenario.started_at).total_seconds()
                        if elapsed > self.scenario_timeout:
                            expired_scenarios.append(scenario_id)
        
        # Close expired scenarios
        for scenario_id in expired_scenarios:
            self.logger.warning(f"⏰ Closing expired scenario {scenario_id}")
            self.complete_scenario(scenario_id, success=False)
            self.close_scenario(scenario_id, force=True)
    
    def _cleanup_completed_scenarios(self):
        """Cleanup scenarios marked for cleanup"""
        scenarios_to_close = []
        
        with self.lock:
            for scenario_id, scenario in self.active_scenarios.items():
                if scenario.status == ScenarioStatus.CLEANUP:
                    scenarios_to_close.append(scenario_id)
        
        # Close scenarios
        for scenario_id in scenarios_to_close:
            self.close_scenario(scenario_id)
    
    def _force_cleanup_oldest(self):
        """Force cleanup of oldest scenarios when at capacity"""
        if not self.active_scenarios:
            return
        
        # Find oldest scenario
        oldest_scenario = min(
            self.active_scenarios.values(),
            key=lambda s: s.created_at
        )
        
        self.logger.warning(f"⚠️ Force closing oldest scenario {oldest_scenario.id}")
        self.complete_scenario(oldest_scenario.id, success=False)
        self.close_scenario(oldest_scenario.id, force=True)
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return 0.0

# Global scenario manager instance
_scenario_manager = None

def get_scenario_manager() -> ScenarioManager:
    """Get global scenario manager instance"""
    global _scenario_manager
    if _scenario_manager is None:
        _scenario_manager = ScenarioManager()
        _scenario_manager.start()
    return _scenario_manager

def create_scenario(intersection_id: str, **kwargs) -> str:
    """Create a new scenario (convenience function)"""
    return get_scenario_manager().create_scenario(intersection_id, kwargs)

def close_scenario(scenario_id: str, force: bool = False) -> bool:
    """Close a scenario (convenience function)"""
    return get_scenario_manager().close_scenario(scenario_id, force)

if __name__ == "__main__":
    # Test scenario manager
    print("🎯 Testing Scenario Manager")
    
    manager = ScenarioManager()
    manager.start()
    
    # Create test scenarios
    scenario1 = manager.create_scenario("intersection_001")
    scenario2 = manager.create_scenario("intersection_002")
    
    print(f"Created scenarios: {scenario1}, {scenario2}")
    
    # Start scenarios
    manager.start_scenario(scenario1)
    manager.start_scenario(scenario2)
    
    # Update progress
    manager.update_scenario_progress(scenario1, vehicles_processed=5, predictions_made=2)
    manager.update_scenario_progress(scenario2, vehicles_processed=3, light_changes=1)
    
    # Get status
    status1 = manager.get_scenario_status(scenario1)
    print(f"Scenario 1 status: {status1}")
    
    # Complete scenarios
    manager.complete_scenario(scenario1)
    manager.complete_scenario(scenario2)
    
    time.sleep(1)
    
    # Get statistics
    stats = manager.get_statistics()
    print(f"Manager statistics: {stats}")
    
    manager.stop()
    print("✅ Test completed")
