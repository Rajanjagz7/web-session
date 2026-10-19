# RebateM8 NSW — Module & Role Documentation

Frontend reference for the modules **Jobs → All**, **Installer**, **Installer Users**,
**Admin Users**, **Activity**, **CMS**, **Matrix**, **Rebates → Products**, **Calculator**,
plus the three role-based login flows (**Master Admin**, **Installer Admin**, **Installer User**).

- **Stack**: React + TypeScript + Vite, Redux Toolkit, Formik + Yup, Tailwind
- **Route table**: [privateRoutes.ts](../src/app/router/privateRoutes.ts) · path constants in [routeConstants.ts](../src/app/router/routeConstants.ts)
- **Sidebar**: [apps.navigation.config.ts](../src/configs/navigation.config/apps.navigation.config.ts)
- **API paths**: [api.constant.ts](../src/constants/api.constant.ts)

---

## 1. Roles

Defined in [roles.constant.ts](../src/constants/roles.constant.ts):

| Constant | Value | Notes |
| --- | --- | --- |
| `MASTER_ADMIN` | `Master Admin` | Platform owner |
| `MASTER_ADMIN_USER` | `Master Admin User` | Platform staff created from Admin Users |
| `ADMIN` | `Installer Admin` | Installer company admin |
| `INSTALLER_USER` | `Installer User` | Installer company member |
| `CONTRACTOR` | `contractor` | Installer-scoped |
| `SALES` | `sales` | Installer-scoped |

Groupings used by the router:

- `MASTER_ONLY` = `Master Admin`, `Master Admin User`
- `INSTALLER_ROLES` = `Installer Admin`, `Installer User`, `contractor`, `sales`
- `ALL_ROLES` = all six

---

## 2. Module → Role access matrix

| Module | Route | Master Admin | Master Admin User | Installer Admin | Installer User |
| --- | --- | :--: | :--: | :--: | :--: |
| Jobs → All | `/jobs` | Yes | Yes | Yes | Yes |
| Jobs → In Progress | `/in-progress-jobs` | Yes | Yes | Yes | Yes |
| Jobs → In Audit | `/in-audit` | No | No | Yes | Yes |
| Jobs → Action Required | `/action-Required-jobs` | Yes | Yes | No | Yes |
| Jobs → Being Assessed | `/being-assessed-jobs` | Yes | Yes | No | Yes |
| Jobs → Completed | `/completed-jobs` | Yes | Yes | No | Yes |
| Jobs → Archived | `/archived-jobs` | Yes | Yes | Yes | Yes |
| Job Detail | `/jobs/:id` | Yes | Yes | Yes | Yes |
| Installer | `/installer`, `/installer/add`, `/installer/:id` | Yes | Yes | No | No |
| Installer Users | `/installeruser` | Yes | Yes | No | No |
| Admin Users | `/admin-users` (+ `/usermanagement`) | Yes | Yes | No | No |
| Activity | `/activity` | Yes | Yes | No | No |
| CMS | `/privacypolicy` | Yes | Yes | No | No |
| Matrix | `/matrix`, `/matrix/:id` | Yes | Yes | No | No |
| Rebates → Products | `/products` | Yes | Yes | No | No |
| Rebates (listing) | `/rebates` | Yes | Yes | Yes | Yes |
| Calculator | `/rebates/calculator` | Yes | Yes | Yes | Yes |
| Statistics | `/rebates/statistics` | Yes | Yes | No | No |
| Invoices | `/invoices` | Yes | Yes | No (route is MASTER_ONLY) | No |
| Dashboard | `/dashboard` | Yes | Yes | Yes | No |
| Company Details | `/companydetails` | No | No | Yes | Yes |
| Workspace | `/workspace` | No | No | Yes | Yes |
| Projects | `/projects` | Yes | Yes | Yes | Yes |
| Profile | `/app/account/settings/profile` | Yes | Yes | Yes | Yes |

> **Known mismatch** — **Invoices** is listed in the sidebar for installer roles, but its route
> authority is `MASTER_ONLY`. An installer-role user who clicks it lands on Access Denied.
> Sources: [apps.navigation.config.ts](../src/configs/navigation.config/apps.navigation.config.ts)
> vs [privateRoutes.ts](../src/app/router/privateRoutes.ts).

---

## 3. Jobs → All

**Route** `/jobs` · **Component** [Jobs.tsx](../src/views/Jobs/Jobs.tsx) · **Store** [src/views/Jobs/store](../src/views/Jobs/store)
**Access** all six roles.

One `Jobs` component backs every Jobs sub-tab (All, In Progress, In Audit, Action Required,
Being Assessed, Completed, Archived). The route pathname decides the header label and the implicit
status filter (`getHeaderLabel` / `getLabelForRoute`). On the **All** tab no status is forced — the
API is called without a `status` param unless the user selects one.

### 3.1 Data flow

```
Jobs.tsx -> dispatch(getJobListMasterAdmin(tableData))
         -> buildJobListQueryParams()   (src/views/Jobs/store/jobListQuery.ts)
         -> GET /v1/jobs?<query>        (src/services/JobService.ts :: getJobList)
         -> mapApiJobToListRow()        (src/views/Jobs/store/jobListMappers.ts)
```

Query params built: `skip`, `limit`, `page`, `sort` (default `createdAt`), `sortType` (default `desc`),
`search`, `status` (multi), `installerId`, `activityType`, `pendingSignature`, `partialTask`,
`customerType`, `originalEquipment`, `isVBARequested`, `isCESRequested`, `auditor`.

Scheme labels map to API `activityType` values:

| UI scheme | `activityType` |
| --- | --- |
| Heating & Cooling | `heating_cooling` |
| Hot Water Heat Pump | `hot_water_heat_pump` |
| Heating Cooling & Hot Water | `heating_cooling_hot_water` |

### 3.2 Table columns

| Column | Key |
| --- | --- |
| Action | — (view / notes icons) |
| Job ID | `jobId` |
| Status | `status` (colour-coded tag from API `statusList`) |
| Customer | `customerName` |
| Company Name | `companyName` |
| Customer Type | `customerType` |
| In Renovation? | `isRenovationJob` |
| Phone Number | `customerPhoneNumber` |
| Address | `customerAddress` |
| Suburb | `suburb` |
| Scheme | `scheme` |
| Installation Date | `activityDate` |
| VEECs | `veecs` |
| Hot Water value | `hotValue` |
| STC value | `stcValue` |

Numeric rebate columns render as `$<formatted>` for installer-admin roles and as raw values
otherwise (`renderJobsNumericRebateCell`).

### 3.3 Filters and search

Component [JobsFilters.tsx](../src/views/Jobs/components/JobsFilters/JobsFilters.tsx),
state hook [useJobsFilters.ts](../src/views/Jobs/components/JobsFilters/useJobsFilters.ts).

- **Search** — free text (`TbSearch`), debounced, maps to `search`
- **Status** — multi-select with coloured options
- **Installer / Company** — lazy-loaded, searchable, paginated select (Master Admin only)
- **Scheme** — Heating & Cooling / Hot Water Heat Pump / …
- **Customer Type**
- **Original Equipment** (Hot Water scheme)
- **Auditor** — lazy-loaded select (currently commented out in the JSX)

Company, customer-type, equipment and auditor filters are conditionally rendered via
`showCompanyFilter` / `showCustomerTypeFilter` / `showEquipmentFilter` / `showAuditorFilter`.

### 3.4 Toolbar actions (role-gated)

| Action | Visible to | Conditions |
| --- | --- | --- |
| **Add Jobs** | Master Admin, Master Admin User, Installer Admin | Hidden for Installer User / contractor / sales. Opens the [AddJobForm](../src/views/Jobs/components/AddJob/AddJobForm.tsx) stepper drawer |
| **Delete** | Master Admin, Master Admin User | Requires row selection. `DELETE /v1/jobs` |
| **Download Upload Form** | Master Admin, Master Admin User | Rows selected, status `Passed Review`, scheme H&C (or HWHP + originalEquipment + customerType), tab In Audit or Complete |
| **Send to VEU** | Master Admin, Master Admin User | Status `Submit API`, tab Complete, activity count ≤ 50 |
| **Upload Job / Upload VEU CSV** | Master Admin roles | Currently commented out in the JSX |

The selected-row count renders in a badge chip beside the toolbar.

### 3.5 Add Job

[src/views/Jobs/components/AddJob](../src/views/Jobs/components/AddJob) — a Formik stepper
(`AddJobStepper`) with dynamic fields (`DynamicFormField`, `addJobFormConfig.ts`), runtime-built
validation (`buildAddJobValidation.ts`), product rows (`AddJobProductsSection`), contractor groups
(`useContractorGroups`) and installer members by role (`useInstallerMembersByRole`).
Submits `POST /v1/jobs`.

### 3.6 Job detail

**Route** `/jobs/:id` · [JobView.tsx](../src/views/Jobs/JobView.tsx) · tabs in [src/views/Jobs/tabs](../src/views/Jobs/tabs)

| Tab | Value | Visible to |
| --- | --- | --- |
| Job Information | `tab1` | all |
| Products | `tab2` | all |
| Post Install Details | `tab3` | all |
| Tasks | `tab4` | all |
| Photos | `tab5` | all |
| Notes | `tab6` | Installer Admin, Master Admin, Master Admin User |
| Audit Checklist | `tab7` | role-gated |
| Activity Logs | `tab8` | role-gated |
| Documents | `tab9` | all |

### 3.7 Key endpoints

| Purpose | Method + path |
| --- | --- |
| List | `GET /v1/jobs` |
| Detail | `GET /v1/jobs/:id` |
| Update | `PATCH /v1/jobs/:id` |
| Create | `POST /v1/jobs` |
| Bulk delete | `DELETE /v1/jobs` |
| Tasks | `GET` / `PATCH` `/v1/jobs/:id/tasks` |
| History | `GET /v1/jobs/:id/history` |
| Unlabelled photos | `GET /v1/jobs/:id/unlabel-photos` |
| Export photos | `GET /v1/jobs/:id/export-photos` |
| Engagement resend | `POST /v1/jobs/:id/engagement/resend` |
| Site assessment | `POST /v1/jobs/:id/site-assessment` |
| Send nomination | `POST /v1/jobs/:id/send-nomination` |
| Export (bulk) | `POST /v1/job/export` |
| Export all (excel) | `GET /v1/job/export/list?scheme=…` |
| Send to VEU | `POST /v1/veu-integration/add/activities` |
| VEU activity count | `POST /v1/veu-integration/activity-count` |
| Audit checklist | `GET /v1/audit/checklist`, `PUT /v1/audit/checklist/update` |
| Notes | `GET` / `POST` `/v1/notes`, `PATCH` / `DELETE` `/v1/notes/:id` |

---

## 4. Installer

**Route** `/installer` (list), `/installer/add`, `/installer/:id` · **Access** Master Admin + Master Admin User only
**Components** [Installer.tsx](../src/views/installer/Installer.tsx),
[AddNewInstaller.tsx](../src/views/installer/AddNewInstaller.tsx),
[AddNewInstallerOtherDetail.tsx](../src/views/installer/AddNewInstallerOtherDetail.tsx)
**Store** [src/views/installer/store](../src/views/installer/store) · **Service** [InstallerService.ts](../src/services/InstallerService.ts)

### 4.1 List columns

| Column | Key |
| --- | --- |
| ID | `installerCode` |
| Company Name | `companyName` |
| Contact Name | `contactName` |
| Assigned Person | `assignedPerson` |
| Activity | `activityScheme` |
| Suburb | `installerSuburb` |
| Status | `installerStatus` |
| $/ESC | `escValue` |
| $/PRC | `prcValue` |
| Team | — (opens team drawer) |
| Active / Inactive | — (toggle) |
| Action | — (edit / delete / impersonate) |

### 4.2 Toolbar actions

- **Add Installer** → `/installer/add`
- **Export Installers** → `GET /v1/installer/export/installer`
- **Export Recycle Info** → `GET /v1/installer/recycle-info/excell`
- **Licence Alert Report** → `GET /v1/installer/license-alert/email`
- **Payment Report** → `GET /v1/installer/payment/report` (downloads `Installer_Payment_Report.xlsx`)
- Search + filters ([InstallerTableSearch.tsx](../src/views/installer/InstallerTableSearch.tsx))

### 4.3 Add / Edit form tabs

| Tab | Value | Availability |
| --- | --- | --- |
| Company Details | `tab1` | always |
| Other Details | `tab2` | edit mode only (`!isAddMode`) |
| Onboarding / Training | `tab3` | edit mode only (`id` present) |

**Other Details** captures: contact name/email, `ESC Value For Admin` / `For User`,
`PRC Value For Admin` / `For User`, `STC Value for Admin` / `For User`, Referred by,
Referral Gift Received, Companies Referred, Accredited Person, Account Name, BSB Number,
Account Number, Benefits to Customer, plus per-role licence sections
([InstallerRoleLicenceSections.tsx](../src/views/installer/components/InstallerRoleLicenceSections.tsx))
and RESA / other training ([OtherRelevantTrainingFields.tsx](../src/views/installer/components/OtherRelevantTrainingFields.tsx)).

### 4.4 Related drawers / dialogs

| File | Purpose |
| --- | --- |
| [ManageInstallerTeam.tsx](../src/views/installer/ManageInstallerTeam.tsx) | Team member list + add/edit member |
| [ManageTeamAccess.tsx](../src/views/installer/ManageTeamAccess.tsx) | Team-level module access |
| [UserModuleAccessDrawer.tsx](../src/views/installer/UserModuleAccessDrawer.tsx) | Per-user permissions (`GET` / `POST` `/v1/installer/user/permission`) |
| [RecyclingHistoryDrawer.tsx](../src/views/installer/RecyclingHistoryDrawer.tsx) | `GET /v1/installer-history/list` |
| [InstallerApproval.tsx](../src/views/installer/InstallerApproval.tsx) | Approval / signature |
| [onboardingSection/](../src/views/installer/onboardingSection) | Onboarding products, admin sign, public email page |

### 4.5 Key endpoints

| Purpose | Path |
| --- | --- |
| List | `GET /v1/installer` |
| Detail / update | `GET` / `PATCH` `/v1/installers/:id` |
| Create (all detail) | `POST /v1/installer/add/all/detail` |
| Add existing user | `POST /v1/installer/add/exist/user` |
| Head admin | `PUT /v1/installers/head-admin` |
| Members | `GET /v1/installers/:id/members`, `…/members/by-role`, `…/members/:userId` |
| Module access | `POST /v1/installer/module/access` |
| Delete | `DELETE /v1/installer/delete/:id` |
| Onboarding | `/v1/installer/onboarding/{add,detail,product,email,sms,sign/add,sign/detail}` |
| Signature | `/v1/installer/signature/{add,detail}`, `/v1/installers/:id/sign/send-sms` |
| Contractor groups | `GET` / `POST` `/v1/contractor-groups` |

---

## 5. Installer Users

**Route** `/installeruser` · **Access** Master Admin + Master Admin User only
**Component** [installerListing.tsx](../src/views/installer/installerListing.tsx)

A cross-company listing of every installer-side user (Installer Admin, Installer User, contractor, sales).

### 5.1 Columns

| Column | Key |
| --- | --- |
| Contact Name | `contactName` |
| Company Name | `installerData` (array — one user can belong to several companies) |
| Email | `email` |
| Phone Number | `phoneNumber` |
| Licence Status | `licenseStatus` |
| Pending Sync Photos | `syncPhotoPendingCount` |
| Last Mobile Access | `lastAccessedAt` |
| Last Web Access | `webLastAccessedAt` |
| Action | edit (pencil) → [EditInstallerUserData.tsx](../src/views/installer/EditInstallerUserData.tsx) |

### 5.2 Actions

- **Export Installer Users** → `GET /v1/user/export`
- **Export Pending Sync Photos** → `GET /v1/user/pending-sync-photo-report/download`
- Search + pagination
- Edit user drawer → member detail `PATCH`
- Remove user from a company → `POST /v1/user/remove/company`

---

## 6. Admin Users

**Route** `/admin-users` (also reachable at `/usermanagement`) · **Access** Master Admin + Master Admin User only
**Components** [UserManagement.tsx](../src/views/UserManagement/UserManagement.tsx),
[AddNewUser.tsx](../src/views/UserManagement/AddNewUser.tsx),
[ManageMasterAdminAccess.tsx](../src/views/UserManagement/ManageMasterAdminAccess.tsx)
**Service** [UserManagementService.ts](../src/services/UserManagementService.ts)

Manages platform-side (Master Admin User) accounts.

### 6.1 Columns

| Column | Key |
| --- | --- |
| User | `firstName` (avatar + full name) |
| Phone Number | `phoneNumber` |
| Email | `email` |
| Action | edit / delete / manage access |

### 6.2 Add / Edit user fields

Profile picture upload, First Name, Last Name, Phone Number (country-code picker, AU default),
Email ID, Password (create mode), `isAuditor` flag, and role — `roleType` is forced to the
admin-user role type (`ADMIN_USER_ROLE_TYPE`).

### 6.3 Endpoints

| Purpose | Path |
| --- | --- |
| List | `GET /v1/users` |
| Create | `POST /v1/users` |
| Detail / update | `GET` / `PATCH` `/v1/users/:id` |
| Roles | `GET /v1/roles` |
| Chat user list | `GET /v1/auth/admin/user/chat` |

---

## 7. Activity

**Route** `/activity` · **Access** Master Admin + Master Admin User only
**Component** [Activity.tsx](../src/views/Activity/Activity.tsx) · **Service** [ActivityService.ts](../src/services/ActivityService.ts)

Read-only platform-wide audit log.

### 7.1 Columns

| Column | Key | Notes |
| --- | --- | --- |
| Date | `createdAt` | `DD/MM/YYYY` + `h:mm A` on two lines |
| Summary | `summary` | not sortable |
| Action | `action` | capitalised tag |
| Actor | `actor` | avatar with initials |
| Company | `company` | |
| View | — | eye icon → detail drawer with the full log payload |

### 7.2 Behaviour

- Search (`TbSearch`), sorting, `CustomPagination`
- Params: `page`, `limit`, `sort`, `sortType`, `search`, `status`
- Endpoint: `GET /v1/activity-logs`
- No create / edit / delete — the module is view-only

---

## 8. CMS

**Route** `/privacypolicy` (sidebar label “CMS”) · **Access** Master Admin + Master Admin User only
**Component** [PrivacyPolicy.tsx](../src/views/CMSPages/PrivacyPolicy/PrivacyPolicy.tsx) · **Service** [CmsService.ts](../src/services/CmsService.ts)

Rich-text content management using **CKEditor 5 (Classic)**.

### 8.1 Content types

| Value | Label |
| --- | --- |
| `Policy` | Privacy Policy |
| `TermsAndCond` | Terms & Condition |
| `Article` | Help |
| `InstallerDeclaration` | Installer Declaration |
| `CustomerDeclaration` | Customer Declaration |
| `CustomerApproval` | Customer Approval |

**Audience**: `Installer`, `Consumer`, `Public` · **Status**: `published`, `draft`

### 8.2 Columns

Title · Type (`displayType`) · Audience · Status · Updated At · Action (edit / delete)

### 8.3 Rules

- Add / edit opens a drawer with title, type, audience, status and a CKEditor HTML body
- Delete is **blocked** for system types: `TermsAndCond`, `Policy`, `CustomerApproval`,
  `CustomerDeclaration`, `InstallerDeclaration` (see `handleDelete`); confirmation via
  [deleteConfirmation.tsx](../src/views/CMSPages/PrivacyPolicy/deleteConfirmation.tsx)

### 8.4 Endpoints

`GET /v1/cms` · `GET /v1/cms/:id` · `POST /v1/cms` · `PATCH /v1/cms/:id` · `DELETE /v1/cms/:id`

---

## 9. Matrix

**Route** `/matrix` (list), `/matrix/:id` (rule detail) · **Access** Master Admin + Master Admin User only
**Components** [Matrix.tsx](../src/views/Matrix/Matrix.tsx),
[MatrixProductDetail.tsx](../src/views/Matrix/MatrixProductDetail.tsx),
[MatrixEditDetail.tsx](../src/views/Matrix/MatrixEditDetail.tsx)
**Service** [MatrixService.ts](../src/services/MatrixService.ts) · **Mappers** [matrixMappers.ts](../src/views/Matrix/matrixMappers.ts)

Defines the photo / evidence rules a job must satisfy, keyed by activity and original equipment.

### 9.1 List columns

| Column | Key |
| --- | --- |
| Rule No | `ruleNo` |
| Activity | `activity` |
| Original Equipment | `originalEquipment` |
| Action | edit / view |

### 9.2 Rule form

Validation: `MatrixRuleValidationSchema`. Three unit groups, each with a count and an
auto-resized photo-set list (`syncPhotoSetCount` → `resizePhotoSet`):

- `existingUnits`
- `decommissioningUnits`
- `newUnits`

Changing a unit count rebuilds `<unitField>.photoSet` to match, preserving existing entries.

### 9.3 Endpoints

`GET /v1/matrix` · `GET /v1/matrix/equipment` · `POST /v1/matrix` · `GET /v1/matrix/:id` · `PUT /v1/matrix/:id`

---

## 10. Rebates → Products

**Route** `/products` · **Access** Master Admin + Master Admin User only
**Component** [Product.tsx](../src/views/Product/Product.tsx) · **Service** [ProductService.ts](../src/services/ProductService.ts)
**Store** [src/views/Product/store](../src/views/Product/store)

Sidebar location: **Rebates** (collapse) → **Products** / **Rebates** / **Calculator** / **Statistics**.

### 10.1 Tabs

| Tab | Value | Meaning |
| --- | --- | --- |
| Uploaded | `uploaded` | Raw products as imported |
| Audited | `updated` | Normalised / reviewed products |

### 10.2 Columns — Uploaded tab

`productCategoryNo` · `brand` · `productModel` · `productConfiguration` · `status` ·
Calculator Status (`isActive`)

### 10.3 Columns — Audited tab

`productCategoryNo` · `brand` · `productModel` · `productConfiguration` · `gemsClass` ·
Heating Capacity kW (`heatingCapacityKW`) · Cooling Capacity kW · `aeer` · `acop` ·
`gemsHspfColdCom` · GEMS HSPF Cold (res) · `gemsHspfMixedRes` · `gemsHspfMixedCom`

### 10.4 Actions

- **Upload** — XLS import (`POST /v1/product/uploadxls`)
- **Export** — `GET /v1/product/export`
- **Merge products** — merge dialog (`POST /v1/product/merge`)
- **Brand normalise / rename** — `POST /v1/product/brand/normalize`
- **Status toggle** — `PATCH /v1/products/status` (drives Calculator Status / `isActive`)
- Search + Category filter (`PRODUCT_CATEGORY_OPTIONS`) + pagination

### 10.5 Endpoints

`GET /v1/products` · `GET /v1/products/brands` · `GET /v1/products/brands/:brand/models` ·
`POST /v1/product/uploadxls` · `PATCH /v1/products/status` · `POST /v1/product/merge` ·
`POST /v1/product/brand/normalize` · `GET /v1/product/export`

---

## 11. Calculator

**Route** `/rebates/calculator` · **Access** all roles
**Components** [RebateCalculator.tsx](../src/views/Rebate/listing/RebateCalculator.tsx) →
[CalculatorForm.tsx](../src/views/Rebate/listing/calculator/CalculatorForm.tsx)
**Config** [activityCalculator.ts](../src/views/Rebate/listing/calculator/activityCalculator.ts) ·
**Mappers** [estimateMappers.ts](../src/views/Rebate/listing/calculator/estimateMappers.ts)

Sidebar: a top-level **Calculator** item for installer roles, and nested under
**Rebates → Calculator** for Master Admin roles.

### 11.1 Modes (Segment control)

| Segment | Behaviour |
| --- | --- |
| `calculator` | Full activity form → estimate |
| `jobId` | [JobIdTab](../src/views/Rebate/listing/calculator/components/JobIdTab.tsx) — estimate from an existing job |

### 11.2 Form fields and options

| Field | Options |
| --- | --- |
| Activity Type | `heating_cooling` (Heating & Cooling), `hot_water_heat_pump` (Hot Water Heat Pump) |
| Building Type | `residential` (Residential Building), `business` (Small Business Site) |
| System Type *(HWHP + residential)* | `heat_pump`, `solar` (Solar, electric boosted) |
| Products | repeatable Brand + Model rows |
| Install Type | `New`, `Replacement` |
| Postcode | 4 digits |
| Existing Fuel *(HWHP + residential)* | `gas`, `electric` |
| Climate Zone *(HWHP, not solar)* | `HP3-AU`, `HP5-AU` |

### 11.3 Conditional logic

`canShowProductFields()` — product / postcode / install-type fields appear once activity and
building type are chosen (and, for Hot Water residential, once system type is chosen).

`resolveProductListParams()` — decides which brand/model catalogue to query:

| Activity + Building + System | Params |
| --- | --- |
| Heating & Cooling | `category=air_conditioner` |
| Hot Water + business | `category=heat_pump_water_heater` |
| Hot Water + residential + heat pump | `category=water_heater&block=heat_pump` |
| Hot Water + residential + solar | `category=water_heater&block=solar` |

### 11.4 Validation (Yup)

- `activityType`, `buildingType` — required
- `systemType` — required when HWHP + residential
- `products` — min 1, each needs brand + model, only when product fields are shown
- `installType`, `postcode` (`/^\d{4}$/`) — required when product fields are shown
- `oldFuel` — required for HWHP + residential
- `climateZone` — required for HWHP unless system type is `solar`

### 11.5 Endpoints

| Purpose | Path |
| --- | --- |
| Estimate | `POST /v1/calculators/estimate` |
| Original equipment | `GET /v1/calculators/original-equipment` |
| Usage list | `GET /v1/calculator-usage/installer/list` |
| Brand list | `GET /v1/product/brand/list` |
| Model list | `GET /v1/product/model/list` |
| Postcode list | `GET /v1/postcode/list` |
| Job rebate | `GET /v1/rebate/generate?jobId=…`, `GET /v1/rebate/stc/generate?jobId=…` |

Results render in [CalculatorResultsPanel](../src/views/Rebate/listing/calculator/components/CalculatorResultsPanel.tsx).

---

## 12. Login flows by role

Auth hook: [useAuth.ts](../src/utils/hooks/useAuth.ts) · Service: [AuthService.ts](../src/services/AuthService.ts)
Landing logic: [getDefaultRoute.ts](../src/shared/utils/getDefaultRoute.ts)

Public routes: `/sign-in`, `/log-in`, `/sign-up`, `/forgot-password`, `/reset-password`
([publicRoutes.ts](../src/app/router/publicRoutes.ts)).

### 12.1 Master Admin / Master Admin User — email + password

**Route** `/log-in` · [LoginForm.tsx](../src/views/auth/LogIn/LoginForm.tsx) ·
Validation `SignInFormValidationMaterAdmin`

1. User enters **Email** and **Password**.
2. `signIn()` → `POST /v1/auth/admin/login`.
3. On success, `applyAuthSession()` stores the session, then `refreshSessionFromMe()`
   calls `GET /v1/auth/me` to hydrate user + authority.
4. `getDefaultRoute(authority)` returns **`/jobs`** (Jobs → All) for platform admins.
   Any `REDIRECT_URL_KEY` query param takes precedence.
5. Failures surface as an inline `Alert` plus a danger notification.

Sign-out for platform admins returns to `appConfig.unAuthenticatedEntryPathForAdmin` (`/log-in`).

Supporting flows: **Forgot Password** (`POST /v1/auth/forgot-password`) and
**Reset Password** (`POST /v1/auth/reset-password`).

### 12.2 Installer Admin — phone + OTP

**Route** `/sign-in` · [SignInForm.tsx](../src/views/auth/SignIn/SignInForm.tsx) ·
Validation `SignInFormValidationInstallerAdmin`

1. Field label is **“Primary Admin Phone Number”**; `react-phone-input-2` with country locked
   to **AU** (`countryCodeEditable={false}`, `onlyCountries` starts with `au`).
2. `sendOtp({ countryCode, phoneNumber })` → `POST /v1/auth/otp/request` (Redux `requestOtp`);
   status passes through `requesting`.
3. A dialog opens with a `react-otp-input` code field, plus **Resend Code** and **Verify Email** actions.
4. `verifyOtp({ countryCode, phoneNumber, code })` → `POST /v1/auth/otp/verify` (Redux
   `verifyOtpLogin`); status passes through `verifying`.
5. On success the thunk returns `landingRoute` from `getDefaultRoute`:
   - **no company selected** → `/workspace` ([WorkSpace/List.tsx](../src/views/WorkSpace/List.tsx))
   - **company selected** → `/jobs`
6. In the workspace the admin picks a company → `POST /v1/auth/select-company`
   (list from `GET /v1/auth/companies`), then lands on `/jobs`.

New installer company sign-up: `/sign-up` → `POST /v1/auth/register-installer`
(+ `POST /v1/auth/register-verify-otp`).

### 12.3 Installer User (and contractor / sales) — phone + OTP

Same `/sign-in` phone + OTP flow as Installer Admin. The differences are post-login:

- `getDefaultRoute` sends them to `/workspace` when no company is selected, otherwise `/jobs`.
- Sidebar is limited to Workspace, Projects, Calculator, Jobs (All / In Progress / In Audit /
  Action Required / Being Assessed / Completed / Archived / Exception Logs), Company Details, Invoices.
- No Dashboard for Installer User — Dashboard authority excludes `INSTALLER_USER`.
- **Add Jobs** is hidden on the Jobs list; **Delete** and the VEU / upload-form actions are hidden.
- Notes tab on job detail is hidden.
- Photo export sends `?type=installer` (`downloadPhotosAPI`).
- Per-user module visibility is further restricted by permissions the Master Admin sets in
  [UserModuleAccessDrawer.tsx](../src/views/installer/UserModuleAccessDrawer.tsx)
  (`GET` / `POST` `/v1/installer/user/permission`).

### 12.4 Impersonation (Master Admin → Installer)

| Action | Endpoint |
| --- | --- |
| Bypass login into an installer account | `POST /v1/auth/bypass-login` |
| Mobile bypass | `POST /v1/installer/bypass/login` |
| Exit impersonation | `POST /v1/auth/exit-impersonation` |

Public token-based pages (no auth): installer login link
`/installerLogin/userId/:userId/workspaceId/:workspaceId/secretKey/:secretKey`,
onboarding admin sign `/onboarding/admin-sign/:installerId`,
nomination `/nomination/sign/:token`, engagement `/engagement/sign/:token`.

### 12.5 Session and guards

- `ProtectedRoute` / `PublicRoute` in [src/app/guards](../src/app/guards) and [src/components/route](../src/components/route)
- `AppRoute` checks a route's `authority` array against `state.auth.authority`; a mismatch routes to `/access-denied`
- Token refresh: `POST /v1/auth/refresh` · Current user: `GET /v1/auth/me` · Logout: `POST /v1/auth/logout`
- Persisted store key: `PERSIST_STORE_NAME` in localStorage, cleared on sign-out

---

## 13. Quick reference — landing route by role

| Role | Login page | Auth method | Landing |
| --- | --- | --- | --- |
| Master Admin | `/log-in` | Email + password | `/jobs` |
| Master Admin User | `/log-in` | Email + password | `/jobs` |
| Installer Admin | `/sign-in` | AU phone + OTP | `/workspace` → `/jobs` |
| Installer User | `/sign-in` | AU phone + OTP | `/workspace` → `/jobs` |
| contractor / sales | `/sign-in` | AU phone + OTP | `/workspace` → `/jobs` |
