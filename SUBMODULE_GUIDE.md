# Git Submodule Management Guide

## Overview
This Smart Traffic AI System project uses Git submodules to manage external dependencies and modular components.

## Current Submodules

### 1. trafficlight
- **Path**: `trafficlight/`
- **Repository**: https://github.com/TonyPhuVN/trafficlight.git
- **Branch**: master
- **Purpose**: Core traffic light control system implementation

## Submodule Commands

### Initialize Submodules (for new clones)
```bash
git submodule init
git submodule update
```

Or in one command:
```bash
git submodule update --init --recursive
```

### Clone Repository with Submodules
```bash
git clone --recurse-submodules https://github.com/TonyPhuVN/trafficlight.git
```

### Update Submodules to Latest
```bash
git submodule update --remote
```

### Update Specific Submodule
```bash
git submodule update --remote trafficlight
```

### Check Submodule Status
```bash
git submodule status
```

### Working with Submodule Changes
```bash
# Enter the submodule directory
cd trafficlight

# Make changes and commit
git add .
git commit -m "Update trafficlight implementation"
git push

# Go back to parent project
cd ..

# Commit the submodule reference update
git add trafficlight
git commit -m "Update trafficlight submodule reference"
```

## Submodule Structure

```
smart_traffic_ai_system/
├── .gitmodules              # Submodule configuration
├── trafficlight/            # Submodule: Core traffic system
│   ├── src/                 # Source code
│   ├── config/              # Configuration files
│   └── README.md            # Submodule documentation
├── src/                     # Main project source
├── config/                  # Main project config
└── README.md                # Main project documentation
```

## Best Practices

### 1. Always Update Submodules After Pulling
```bash
git pull
git submodule update --init --recursive
```

### 2. Commit Submodule Reference Changes
When you update a submodule, always commit the reference change in the parent project:
```bash
git add .gitmodules trafficlight
git commit -m "Update submodule references"
```

### 3. Use Specific Branches
Configure submodules to track specific branches for stability:
```bash
git config -f .gitmodules submodule.trafficlight.branch master
```

### 4. Check Before Committing
Always check submodule status before committing:
```bash
git submodule status
git status
```

## Troubleshooting

### Issue: "fatal: No url found for submodule path"
**Solution**: Ensure .gitmodules file exists and is properly configured:
```bash
git submodule sync
git submodule update --init
```

### Issue: Submodule appears as modified but no changes
**Solution**: Update submodule reference:
```bash
cd trafficlight
git checkout master
cd ..
git add trafficlight
git commit -m "Update submodule reference"
```

### Issue: Cannot access submodule repository
**Solution**: Check network connection and repository permissions:
```bash
git submodule sync --recursive
git submodule update --init --recursive
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
steps:
  - name: Checkout with submodules
    uses: actions/checkout@v3
    with:
      submodules: recursive
      
  - name: Update submodules
    run: git submodule update --remote --recursive
```

### Docker Build Example
```dockerfile
# Clone with submodules
RUN git clone --recurse-submodules https://github.com/TonyPhuVN/trafficlight.git

# Or if already cloned
RUN git submodule update --init --recursive
```

## Development Workflow

### 1. Starting Development
```bash
# Clone project
git clone --recurse-submodules <repository-url>
cd smart_traffic_ai_system

# Verify submodules
git submodule status
```

### 2. Regular Updates
```bash
# Update main project
git pull origin master

# Update all submodules
git submodule update --remote --recursive

# Commit submodule updates if needed
git add .
git commit -m "Update submodules to latest versions"
```

### 3. Adding New Submodules
```bash
# Add new submodule
git submodule add <repository-url> <path>

# Commit the addition
git add .gitmodules <path>
git commit -m "Add new submodule: <name>"
```

## Security Considerations

1. **Repository Access**: Ensure all team members have access to submodule repositories
2. **Branch Protection**: Use protected branches for submodule repositories
3. **Dependency Management**: Regularly update submodules for security patches
4. **Access Control**: Manage permissions carefully for submodule repositories

## Maintenance

### Monthly Tasks
- [ ] Update all submodules to latest versions
- [ ] Check for security vulnerabilities in submodules
- [ ] Verify all submodule links are working
- [ ] Update documentation if submodule structure changes

### Before Releases
- [ ] Freeze submodule versions to specific commits
- [ ] Test all functionality with current submodule versions
- [ ] Document submodule versions in release notes
- [ ] Create backup of current submodule state

---

For more information about Git submodules, see: https://git-scm.com/book/en/v2/Git-Tools-Submodules
