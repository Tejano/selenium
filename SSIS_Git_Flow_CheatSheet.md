# SSIS Project Git Flow (Recommended)

This guide outlines how to manage SSIS development, testing, and deployment using Git branches, aligned with modern React/microservices workflows.

---

## 📁 Branch Structure

```bash
main/master      → Production-ready SSIS packages
uat              → Packages approved in UAT
qa               → Packages approved in QA
develop          → Latest validated development changes
feature/*        → Active feature or fix branches
```

---

## 🔁 Development Lifecycle

### 1. Create a feature branch

```bash
git checkout develop
git checkout -b feature/your-fix-name
```

- Work on your `.dtsx`, `.dtproj`, and parameter updates
- Test in DEV environment
- Commit frequently

### 2. Merge to `develop` (after unit testing)

```bash
git checkout develop
git merge feature/your-fix-name
git push origin develop
```

- Only merge if unit tested
- `develop` becomes the **staging point for QA**

---

## 🚦 QA and UAT Promotion

### Promote to QA

```bash
git checkout qa
git merge develop
```

- Update parameters for QA DBs/paths
- Build `.ispac`, deploy to QA environment
- Commit parameter changes to `qa` branch

### Promote to UAT

```bash
git checkout uat
git merge qa
```

- Update for UAT DBs/paths
- Deploy `.ispac` to UAT server

---

## 🚀 Production Deployment

```bash
git checkout master
git merge uat
```

- Update for PROD DBs/paths
- Build `.ispac` and hand off to DBA

---

## 🧠 Tips

- Never edit `develop` directly — always use `feature/*` branches
- Parameter updates per env should stay in that branch (dev → dev values, qa → qa values, etc.)
- Each `.ispac` build is traceable to a specific commit + env

---

## 📦 Folder Organization Example

```
develop/
├── ProjectA/
│   ├── .dtsx, .dtproj
│   └── jobs/
├── ssis-config/
│   ├── schema/
│   └── sprocs/
└── multi-project-jobs/
```

---

For automation ideas, import/export scripts, or CI/CD integration, see the `/export-tools` folder or contact the repo admin.