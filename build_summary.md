# Build Summary Report

## 📦 Project: ios_app

- **Project Type**: `ios`
- **Build Status**: ❌ Failed

**Commands Executed**:
```
(.) $ git reset --hard
(.) $ git fetch
(.) $ git checkout master
(.) $ git pull origin master
(HostApp) $ export GIT_SSL_NO_VERIFY=true
(HostApp) $ pod repo remove gitlab-macys-mobile-ios-podspecs
(HostApp) $ pod repo update fds-mobile-ios-podspecs
(HostApp) $ pod cache clean --all
(HostApp) $ fastlane install
```

**Details**:
```
Command failed in 'HostApp': fastlane install\
```

---
