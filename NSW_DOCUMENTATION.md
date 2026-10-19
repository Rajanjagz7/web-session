# NSW RebateM8 Mobile — Project Documentation

This document describes the **current** React Native codebase as inspected in the repository. Statements that cannot be verified from source are marked **Not identified in the current codebase**. Secret values that appear in source (API keys, passwords, tokens, licenses) are replaced with `[REDACTED]`.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Project Structure](#2-project-structure)
3. [Technology Stack](#3-technology-stack)
4. [Application Architecture](#4-application-architecture)
5. [Navigation](#5-navigation)
6. [API Documentation](#6-api-documentation)
7. [Database / Local Storage](#7-database--local-storage)
8. [Image / File Handling](#8-image--file-handling)
9. [Location](#9-location)
10. [Authentication & Security](#10-authentication--security)
11. [Environment Configuration](#11-environment-configuration)
12. [iOS Configuration](#12-ios-configuration)
13. [Android Configuration](#13-android-configuration)
14. [Third-Party Services](#14-third-party-services)
15. [Important Business Logic](#15-important-business-logic)
16. [Offline / Sync Architecture](#16-offline--sync-architecture)
17. [Build & Run Instructions](#17-build--run-instructions)
18. [Common Issues / Troubleshooting](#18-common-issues--troubleshooting)
19. [Important Files](#19-important-files)
20. [Developer Onboarding](#20-developer-onboarding)
21. [Known Technical Debt / Risks](#21-known-technical-debt--risks)

---

## 1. Project Overview

### What the application does

**NSW RebateM8** (`nsw_rebateM8` / display name **NSW Rebate M8**) is a field-installer mobile app for NSW energy-rebate work. Installers and installer admins:

- Log in with a mobile number and OTP, then select a company (installer).
- View, create, and edit jobs (customer/site engagement, products, team assignment).
- Capture geo-tagged job photos (existing / decommissioning / new equipment, extra photos), store them locally, and upload/sync them.
- Calculate rebates (mobile calculator APIs).
- Manage company profile, team members, notes, notifications, help CMS content, and related job/site/quote/gallery flows (some of these screens remain registered even when hidden from the profile menu).

The app is designed to keep working when the device is offline: jobs and task photos are packed into **Realm**, then uploaded when connectivity returns (foreground timers, reconnect, app-open, and OS background fetch).

### Platforms

- **iOS** (`ios/nsw_rebateM8`, bundle id `org.rebatem8.nsw.au.com`)
- **Android** (`android/app`, application id `com.nsw_rebatem8`)

Portrait orientation is enforced on both platforms.

### Framework and React Native version

| Item | Value |
| --- | --- |
| Framework | React Native |
| React Native | `0.84.0` (`package.json`) |
| React | `19.2.3` |
| Language | TypeScript (strict) with some JavaScript files (`.js`) still in use |
| New Architecture | Enabled (`newArchEnabled=true`, `RCTNewArchEnabled` in Info.plist) |
| JS engine | Hermes (`hermesEnabled=true` on Android; `:hermes_enabled => true` in Podfile) |

### Overall architecture

The app is a **single React Native binary** with:

1. **UI layer** — screens under `src/screen/<domain>/`, shared components under `src/components/`.
2. **State** — Redux Toolkit store (`src/store/store.ts`) with **redux-saga** side effects and **redux-injectors** for per-screen reducer/saga injection.
3. **Networking** — apisauce `Api` base class (`src/sharedUtils/services/api/api.ts`) extended by a large feature API singleton (`src/screen/auth/redux/model/api.ts`).
4. **Local database** — Realm (`src/store/RealmService.ts`, schema version **8**).
5. **Session persistence** — AsyncStorage for tokens, user, and installer/company.
6. **Offline photo/job sync** — `src/services/backgroundSync.ts` + `src/services/backgroundSyncRunner.ts`, triggered from the bottom-tab shell via `useBackgroundJobSync`.
7. **Push** — Firebase Cloud Messaging (`@react-native-firebase/app` + `messaging`) plus a custom Android local-notification native module.

There is no separate `src/navigation/` folder; navigation lives in `src/screen/navigator/`.

---

## 2. Project Structure

### Top-level layout

| Path | Purpose |
| --- | --- |
| `App.tsx` | Root providers (Redux, Safe Area), toast, FCM foreground handler, notification deep-link routing. **No feature business logic beyond notifications.** |
| `index.js` | `AppRegistry`, FCM background handler, BackgroundFetch headless task registration. |
| `app.json` | App name `nsw_rebateM8`, display name `NSW Rebate M8`. |
| `package.json` | Dependencies, scripts, Node engine. |
| `yarn.lock` | Lockfile (Yarn is the package manager in this repo). |
| `metro.config.js` | Default Metro config. |
| `babel.config.js` | `@react-native/babel-preset` + `react-native-worklets/plugin`. |
| `tsconfig.json` | Extends `@react-native/typescript-config`; path alias `@src/*` → `src/*`. |
| `Gemfile` | CocoaPods / Ruby gems for iOS. |
| `firebase.json` | React Native Firebase messaging/crashlytics flags. |
| `patches/` | `patch-package` patch for `react-native-phone-number-input@2.1.0`. |
| `__tests__/App.test.tsx` | Jest smoke test. |
| `android/` | Android native project. |
| `ios/` | iOS native project (`nsw_rebateM8`). |
| `src/` | Application source. |
| `.env.staging` | Staging env file (see [Environment Configuration](#11-environment-configuration)). |
| `README.md` | Default React Native getting-started notes (not project-specific). |

### `src/` layout

| Path | Role |
| --- | --- |
| `src/screen/` | Feature screens and domain Redux. |
| `src/components/` | Shared UI (Theme*, job items, camera/gallery sheets, OCR sheet, etc.). |
| `src/store/` | Redux store, root reducer, root saga, Realm singleton. |
| `src/services/` | Background job/photo sync (JS). |
| `src/sharedUtils/services/api/` | Base HTTP client, API problem mapping, device headers, default base URL. |
| `src/sharedUtils/slices/` | Unused leftover slices (`globalSlice.ts`, `api.ts`) — **not registered** in `rootReducer.ts`. |
| `src/utils/` | Colors, fonts, helpers, image pick/upload, GPS/EXIF, AsyncStorage wrappers, constants. |
| `src/hooks/` | Shared hooks. Currently `useBackgroundJobSync.ts` only. |
| `src/assets/` | Images and SVG XML strings, exported as `Assets` from `src/assets/index.js`. |
| `src/Translator/` | i18n: `i18n.js`, `english.json`, `chinese.json`. |
| `src/types/` | `RootState` type re-export. |
| `src/context/` | **Not identified in the current codebase** (folder not present). |

### Feature domains (`src/screen/`)

| Folder | Purpose |
| --- | --- |
| `auth/` | Login, OTP, company select, language, terms, session Redux + **all HTTP methods**. |
| `splashScreen/` | Cold start: permissions, session restore, Realm open, FCM routing. |
| `navigator/` | Root stack + bottom tabs. |
| `home/` | Job list (`JobListScreen`) and NSW task/photo detail (`TaskDetailScreen`). |
| `jobs/` | Add/edit job stepper, job detail (legacy), notes, local photo list, Realm models, sync helpers. |
| `job13a/` | Glazed / “13A” jobs (parallel screens, APIs, Realm model files). |
| `RebateCalculator/` | Current rebate calculator UI + Redux (wired in navigator and tabs). |
| `calculator/` | Older calculator screen + `rebateRedux.ts` (still registered in the store). |
| `site/` | Sites / projects. |
| `quotes/` | Site-inspection quotes. |
| `team/` | Team member list/add/edit. |
| `company/` | Company profile (`EditCompany.tsx`). |
| `profile/` | Profile drawer and edit profile. |
| `notification/` | Notification list. |
| `gallery/` | Job photo gallery. |
| `library/` | Resource library. |
| `rewards/` | Rewards. |
| `help/` | Help CMS. |
| `CRM/` | Terms and privacy policy screens. |

### Where things live

| Concern | Location |
| --- | --- |
| Screens | `src/screen/<domain>/` (`*Screen.tsx` or named screens such as `EditCompany.tsx`) |
| Shared components | `src/components/` |
| Hooks | `src/hooks/` (plus inline hooks in screens, e.g. `useBottomTabSharedLogic` in `BottomTab.tsx`) |
| Utilities | `src/utils/` |
| HTTP services | `src/sharedUtils/services/api/` (base) + `src/screen/auth/redux/model/api.ts` (all feature endpoints) |
| Redux slices | `src/screen/<domain>/redux/*.ts` registered in `src/store/rootReducer.ts` |
| Sagas | Same Redux files; composed in `src/store/rootSaga.ts` |
| Navigation | `src/screen/navigator/index.tsx`, `BottomTab.tsx` |
| Database | Realm via `src/store/RealmService.ts` and `src/screen/jobs/realmModel/` |
| Assets | `src/assets/` |
| Configuration | `src/sharedUtils/services/api/api-config.ts`, `src/utils/AppConstant.tsx`, native Gradle/Xcode, `.env.staging` |

---

## 3. Technology Stack

| Area | Identified from the project |
| --- | --- |
| React Native | `0.84.0` |
| React | `19.2.3` |
| TypeScript | `^5.8.3` (`tsconfig.json` `strict: true`; JS files still allowed via `allowJs`) |
| Node | `engines.node`: `>= 22.11.0` |
| Package manager | **Yarn** (`yarn.lock` present; no `package-lock.json`) |
| State management | Redux Toolkit `^2.12.0` + `react-redux` `^9.3.0` |
| Side effects | `redux-saga` `^1.5.0` + `redux-injectors` `^2.1.0` |
| Navigation | `@react-navigation/native` `^7.2.5`, stack `^7.9.3`, bottom-tabs `^7.16.2` |
| Database | Realm `^20.2.0` |
| Key-value storage | `@react-native-async-storage/async-storage` `^3.1.1` |
| Networking | `apisauce` `^3.2.2` (wraps Axios), `axios` `^1.16.1`, raw `fetch` / XHR / `RNFS.uploadFiles` for some uploads |
| Image / camera | `react-native-image-crop-picker`, `@react-native-camera-roll/camera-roll`, `react-native-fast-image`, `react-native-compressor` (video), `react-native-heic-converter` |
| Documents | `@react-native-documents/picker` |
| Location | `react-native-background-geolocation` `4.19.2`, `react-native-geolocation-service`, `react-native-geocoding`, `react-native-google-places-autocomplete` |
| Auth | OTP + bearer/refresh tokens (no OAuth SDK). Session in AsyncStorage. |
| Push | `@react-native-firebase/app` + `messaging` `^24.0.0`, `@react-native-community/push-notification-ios`, custom `LocalPushNotificationModule` (Android) |
| Analytics / crash reporting | `@react-native-firebase/crashlytics` is **not** a `package.json` dependency. `firebase.json` sets `crashlytics_debug_enabled: true` but Crashlytics is **not identified as integrated in JS**. SmartLook / GetStream keys exist in `AppConstant.tsx` but are **not referenced** elsewhere. |
| i18n | `i18next` + `react-i18next` |
| UI extras | Reanimated, Gesture Handler, Safe Area, Screens, SVG, Lottie, Toast, Signature canvas, Pell rich editor, WebView, Video, FlashList, responsive-screen |
| Background | `react-native-background-fetch` `^4.4.2` |
| Env | `react-native-config` is a dependency but **no `Config.` usage** was found in source |
| Other | `moment`, `uuid`, `react-native-device-info`, `react-native-permissions`, `react-native-fs`, `react-native-aws3`, `react-native-inappbrowser-reborn`, `react-native-version-check`, `react-native-restart`, `patch-package` |

**Not identified in the current codebase:** Stripe, CodePush, App Center, Ant Media.

---

## 4. Application Architecture

### Data flow (high level)

```
Screen / hook
  → dispatch Redux action  and/or  call api.* directly
      → saga (if the action has a watcher) calls api.*
          → apisauce (Bearer + device headers)
              → REST API (DEFAULT_API_CONFIG.url)
      → on success: reducer updates Redux
  → Realm writes for offline jobs/photos (nswRealmFunctions / realmFunctions)
  → AsyncStorage for tokens, userData, installerData
```

Many screens **bypass sagas** and call `api` from `src/screen/auth/redux/model/api.ts` directly (login, OTP, add job, photo upload, notes, company, etc.). Sagas are used mainly for list loading (jobs, notifications, quotes, gallery, library, team, rewards, calculator catalogs, sites).

### Redux / store

File: `src/store/store.ts`

- `configureStore` with saga middleware and `redux-injectors` enhancer.
- `createReducer` merges `staticReducers` with injected slices.
- Action `auth/logout` resets the entire store to `undefined`.
- Serializable check ignores `auth.socketClient` and `auth.realmInstance` (Realm instance is stored on the auth slice).

Static slices (`src/store/rootReducer.ts`):

| Key | Source |
| --- | --- |
| `auth` | `src/screen/auth/redux/AuthRedux.ts` |
| `jobs` | `src/screen/jobs/redux/JobRedux.ts` |
| `site` | `src/screen/site/redux/SiteRedux.ts` |
| `rebates` | `src/screen/calculator/redux/rebateRedux.ts` |
| `jobs13a` | `src/screen/job13a/redux/Job13Redux.ts` |
| `quotes` | `src/screen/quotes/redux/quotesRedux.ts` |
| `gallery` | `src/screen/gallery/redux/galleryRedux.ts` |
| `library` | `src/screen/library/redux/libraryRedux.ts` |
| `teamMember` | `src/screen/team/redux/teamMemberRedux.ts` |
| `notification` | `src/screen/notification/redux/notificationRedux.ts` |
| `rewards` | `src/screen/rewards/redux/rewardsRedux.ts` |
| `jobsRedux` | `src/screen/home/redux/jobsRedux.ts` (NSW job list + job photos) |
| `rebateCalculator` | `src/screen/RebateCalculator/redux/RebateCalculatorRedux.ts` |

Root saga (`src/store/rootSaga.ts`) starts one watcher per domain listed above.

Screens often **re-inject** the same reducers/sagas with `useInjectReducer` / `useInjectSaga` (duplicate registration of already-static slices).

### Saga / API flow

Typical list pattern (example: NSW jobs in `jobsRedux.ts`):

1. Screen dispatches `jobsReduxActions.jobList({ skip, installerId, search, ... })`.
2. `takeLatest` runs `getJobList`.
3. Saga builds query string and calls `apis.getJobsList(param)` → `GET jobs?...`.
4. Success maps `res.data.jobs` + `statusList` colors into Redux.

Auth interceptors live on the API class, not in sagas (see [Authentication](#10-authentication--security)).

### Local database flow

- Splash (after authenticated session) and OTP verify call `RealmService.getInstance()` and dispatch `authActions.storeRealMObject`.
- NSW job list packing: `JobListScreen.packJobsToRealm` writes `NswJobList` + `NswJobTasks` via `nswRealmFunctions.ts`.
- Photo capture updates `NswPhotoSet` fields (`localUri`, `needsSync`, lat/long, etc.).
- Background sync reads unsynced photos and POSTs them; on success `markNswPhotoSetUploaded`.
- Legacy path still uses `TaskDetails.data` as a JSON string plus `SyncJob` flags (`src/screen/jobs/realmModel/realmFunctions.js`).

### Offline / online behaviour

See [Offline / Sync Architecture](#16-offline--sync-architecture). In short:

- Connectivity: `@react-native-community/netinfo` in splash, login, bottom tabs, and sync engine.
- Offline login restore: `restoreOfflineSessionFromCache` in `AuthRedux.ts`.
- Offline jobs UI: `JobListScreen` reads `getNswJobList(realm)`.
- Offline banner: bottom tab bar shows “You are offline!” when `NetInfo` reports disconnected.

### How screens talk to services / state / database

| Mechanism | When used |
| --- | --- |
| `useSelector` / `useDispatch` | Auth user, installer, Realm instance, lists, loaders |
| Direct `api.method(...)` | Most mutations and many reads |
| Sagas | Paginated lists and some catalog loads |
| Realm helpers | Offline cache, photo `needsSync`, job packing |
| AsyncStorage helpers | `src/utils/AsyncStorage.ts` (`userData`, `installerData`, language, etc.) |

---

## 5. Navigation

Root navigator: `src/screen/navigator/index.tsx`.

- `NavigationContainer` with `setNavigator` (`src/utils/NavigationRef.ts`).
- Stack: `@react-navigation/stack` with `TransitionPresets.SlideFromRightIOS`.
- `headerMode: false`.
- `initialRouteName`: `"splashScreen"`.
- `onStateChange` stores `global.currentScreen`.

There is **no route-name enum** in use. `src/utils/Constants.tsx` defines a small `NavigationScreen` map that **does not match** the actual stack names. Screens navigate with **string literals**.

### Stack screens (actual `name` values)

| Route name | Component |
| --- | --- |
| `splashScreen` | `SplashScreen` |
| `languageSetting` | `LanguageSelection` |
| `loginScreen` | `LoginScreen` |
| `OTPScreen` | `OtpVerificationScreen` |
| `terms` | `Terms` |
| `companyListScreen` | `CompanyListScreen` |
| `editOtpScreen` | `EditOtpScreen` |
| `bottomTab` | `BottomTab` |
| `editProfile` | `EditProfileScreen` |
| `profileDrawer` | `ProfileDrawerScreen` |
| `teamListScreen` / `addTeamScreen` / `editTeamMember` | Team screens |
| `editCompanyScreen` | `EditCompany` |
| `rewardListScreen` / `rewardDetailScreen` | Rewards |
| `termsScreen` / `policyScreen` | CRM legal |
| `jobDetailScreen` | `JobDetailScreen` (legacy job UI) |
| `homeTaskDetailScreen` | `TaskDetailScreen` (NSW tasks/photos) |
| `customerApprovalScreen` | `CustomerApprovalScreen` |
| `notificationListScreen` | Notifications |
| `libraryListScreen` | Library |
| `rebateCalculatorScreen` | `RebateCalculatorScreen` |
| `quotesListScreen` / `addQuotesScreen` / `quoteDetailsScreen` / `quoteCommentListScreen` | Quotes |
| `galleryListScreen` / `galleryDetailScreen` | Gallery |
| `savedJobListScreen` / `archivedJobListScreen` | Job lists |
| `noteListScreen` | `NotesScreen` |
| `helpScreen` | Help |
| `addJobScreen` | `AddJobScreen` |
| `addSiteScreen` / `siteDetailScreen` / `savedSiteListScreen` / `projectNotesScreen` | Sites |
| `13AllJobListScreen` / `noteAListScreen` / `jobADetailScreen` / `uploadedJobAScreen` | Job 13A |
| `localPhotoListScreen` | `LocalPhotoList` |

**Not identified as a registered route:** `messageListScreen` (still targeted from `App.tsx` notification handler).

`BottomTabLegacy.tsx` exists but is **not** used by `index.tsx`.

### Bottom tabs (`src/screen/navigator/BottomTab.tsx`)

Tabs depend on `userData.roleId.roleName === 'installerAdmin'`:

| Role | Tabs (order) |
| --- | --- |
| Installer admin | Jobs, Calculator, Add Job, Profile |
| Other (install user) | Jobs, Help, Add Job, Calculator, Profile |

Icons/labels: `src/screen/navigator/tabArrayData.tsx`.

Deep-link-style param `activeTab` maps legacy names (`Job`, `Rebate Calculator`, `Site Inspection`, `Sync`, `Notification`) onto tab routes or `notificationListScreen`.

### Authentication / navigation flow

```
splashScreen
  ├─ no tokens / logged-out     → loginScreen
  ├─ tokens but no company      → companyListScreen
  ├─ authenticated + company    → bottomTab (Jobs)
  └─ cannot-connect + cache     → bottomTab using cached user/company (offline)

loginScreen
  → OTPScreen (sendOTP)
      → applyVerifyOtpToStore
          ├─ no companies → toast / stay
          └─ companies    → companyListScreen
              → selectCompany → restoreAuthSessionOnLaunch → bottomTab
```

Splash also requests camera, location, and (iOS) photo library before session restore.

### Protected / private screens

There is **no navigation guard component**. Access is by **resetting the stack** after splash/OTP/company select. Private screens are everything after `bottomTab`. If a user is logged out (`forceAuthLogout`), the app `navigateWithReset('loginScreen')`.

---

## 6. API Documentation

### Service files

| File | Role |
| --- | --- |
| `src/sharedUtils/services/api/api-config.ts` | Base URL + 20s timeout |
| `src/sharedUtils/services/api/api.ts` | `Api` class: GET/POST/PUT/PATCH/DELETE + `awsUploadFile` (PUT binary) |
| `src/sharedUtils/services/api/api-problem.ts` | Maps apisauce problems to `{ kind }` |
| `src/sharedUtils/services/api/deviceHeaders.ts` | `x-platform`, `x-app-version`, `x-device-id` |
| `src/screen/auth/redux/model/api.ts` | **All feature endpoints** (singleton subclass of `Api`) |
| `src/sharedUtils/slices/api.ts` | Separate unused `get('options')` client — **not used by the store** |

**Active base URL** (hardcoded, `api-config.ts`):

```
https://nswdev.rebatem8.com.au/api/v1/
```

Commented alternatives in the same file: `nswstage.rebatem8.com.au`, `nsw.rebatem8.com.au`. Timeout: **20000 ms**.

Typical JSON envelope (typed in `AuthRedux.ts` as `ApiEnvelope<T>`):

```ts
{
  success: boolean;
  statusCode: number;
  message?: string;
  data: T | null;
  error?: { code: string; details?: unknown };
}
```

Many methods still accept untyped `body` / `params`. Response field shapes below are listed **only where types or call-site mapping exist**.

### Authentication

Unless noted, requests send `Authorization: Bearer <accessToken>` plus device headers (`x-platform`, `x-app-version`, `x-device-id`). Bypass URLs (no refresh retry): `auth/otp/request`, `auth/otp/verify`, `auth/refresh`, `auth/logout` (`isAuthBypassUrl`).

| Method | HTTP | Endpoint | Purpose | Request | Response (identified) | Auth | Primary callers |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `sendOTP` | POST | `auth/otp/request` | Request SMS OTP | `{ countryCode, phoneNumber }` | `{ success, message }` used at call site | No bearer required | `LoginScreen`, `OtpVerificationScreen` (resend) |
| `verifyOTP` | POST | `auth/otp/verify` | Verify OTP | `{ countryCode, phoneNumber, code, fcmToken }` | `data`: `user`, `companies`, `accessToken`, `refreshToken` (`OtpVerifyData`) | Device headers | `OtpVerificationScreen` |
| `getAuthMe` | GET | `auth/me` | Current user + company | — | `data`: `user`, `company` (`AuthMeData`) | Bearer | `restoreAuthSessionOnLaunch` |
| `getCompanyList` | GET | `auth/companies` | Companies for user | — | Used as `{ success, data }` | Bearer | Auth saga `getAllCompany` |
| `selectCompany` | POST | `auth/select-company` | Bind session to installer | Body from `CompanyListScreen` | `data`: `company`, `accessToken` (`SelectCompanyData`) | Bearer | `CompanyListScreen` |
| `refreshAuthToken` / interceptor | POST | `auth/refresh` | Rotate tokens | `{ refreshToken }` or `{}` if cookie session | Tokens in body and/or headers | Refresh token / cookies | Interceptors, `acquireTokensFromSession` |
| `logout` | POST | `auth/logout` | Server logout | `{}` | Not identified beyond HTTP | Bypass list | Logout flows |
| `getAuthSessions` | GET | `auth/sessions` | List device sessions | — | `DeviceSession[]` typed, call sites not fully traced | Bearer | API method exists |
| `revokeAuthSession` | DELETE | `auth/sessions/:sessionId` | Revoke session | — | Not identified | Bearer | API method exists |
| `userLoginBackFromWeb` | POST | `auth/mobile-bypass-login` | Web-to-mobile login bypass | `body` | Not identified | Not identified | API method exists |

Token extraction also reads `x-access-token`, `x-refresh-token`, `Authorization`, and `Set-Cookie`.

### User / profile

| Method | HTTP | Endpoint | Purpose | Request (identified) |
| --- | --- | --- | --- | --- |
| `updateUserTerms` | PUT | `/user` | Update user (terms) | `body` |
| `editUserProfile` | PUT | `user/` | Edit profile | `body` |
| `sendEditOTP` | POST | `user/send-otp-edit` | OTP for profile contact change | `body` |
| `verifyEditOTP` | POST | `user/verify-otp-edit` | Verify edit OTP | `body` |
| `setFCMUser` | POST | `user/fcm-token` | Register FCM token | `body` — called from `WorkScreen.tsx` |
| `lookupUser` | GET | `users/lookup?countryCode=&phoneNumber=&email=` | Find existing user | Query params; 404 treated as `{ success: true, data: null }` |

### Storage / files

| Method | HTTP | Endpoint | Purpose | Notes |
| --- | --- | --- | --- | --- |
| `presignUpload` | POST | `storage/presign-upload` | Presign upload | Body typed `PresignUploadBody` (`scope`, `refId`, `docType`, `fileName`, `contentType`). Response typed `{ key, url, expiresInSec }`. |
| `presignedUrl` | POST | `storage/presigned-url` | Presigned PUT URL | Mapped in `presignedUpload.ts` as `presigned_url`, `public_link`, `filename`. |
| `presignDownload` | POST | `storage/presign-download` | Presign download | `body` |
| `uploadPhotoWithMetadata` | POST | `file/upload-media` | Multipart media | Also used via raw `fetch` in `UploadImage.ts` **without** attaching Bearer in that helper |
| `uploadTaskPhoto` helper | POST | `file/upload-media-with-location` | Multipart + location | `UploadTaskPhotos.tsx` raw `fetch`; **no Bearer** in that helper |
| `awsUploadFile` | PUT | Caller-supplied URL | Binary PUT to presigned URL | `Content-Type: application/octet-stream` |
| `uploadJobTaskPhoto` | POST | `jobs/:jobId/tasks/:taskId/photos/:photoId/upload` | NSW task photo upload | `FormData`: `file`, `captureDate`, `lat`, `long`, `address`, optional `captureId`, `userName`, `resolutions`, `label`. Uses `fetch` + Bearer. |

### Installers / team / company

| Method | HTTP | Endpoint |
| --- | --- | --- |
| `getTeamMembersList` | GET | `installers/:installerId/members` optional `?search=` |
| `getTeamMembersByRole` | GET | `installers/:installerId/members/by-role?role=` |
| `addTeamMember` / `addExistingTeamMember` | POST | `installers/:installerId/members` |
| `updateTeamMember` | PUT | `installers/:installerId/members/:userId` |
| `removeTeamMember` | DELETE | `installers/:installerId/members/:userId` |
| `getTeamMemberInfo` | GET | `installers/:installerId/members/:userId` |
| `getCompanyDetails` | GET | `installers/:installerId` |
| `editCompanyDetails` | PUT | `installers/:installerId` |
| `requestToChangeBankDetails` | POST | `installers/requestchange` |
| `uploadDocument` | POST | `installer/file` |
| `getLibraryList` | GET | `installer/library` + params |
| `removeCompanyPhoto` | POST | `installer/delete/file` |
| `getHelpChatChannelForInstallerUser` | GET | `installer/help/channel?installerId=` |
| `getLeadGeneratorList` | GET | `installer/filter/list` + param |
| `emailSentCount` | POST | `installer/send/signature/email` |

### NSW jobs (preferred newer API)

| Method | HTTP | Endpoint | Purpose |
| --- | --- | --- | --- |
| `getJobsList` | GET | `jobs` + query | List jobs. Home saga uses `limit=20&sort=createdAt&sortType=desc&skip=&search=&installerId=&activityType=&status=` |
| `getJobDetail` | GET | `jobs/:jobId` | Job detail |
| `getJobTasks` | GET | `jobs/:jobId/tasks` | Tasks + photo sets (packed to Realm) |
| `postJobTask` | PATCH | `jobs/:jobId/tasks` | Add/edit/delete product task. Strips `indoorHeadQuantity` before send |
| `getJobPhotos` | GET | `jobs/:jobId/photos` + params | Synced photos gallery (`skip`, `limit` from saga) |
| `updateJob` | PATCH | `jobs/:jobId` | Update job |
| `postJobSiteAssessment` | POST | `jobs/:jobId/site-assessment` | Site assessment |
| `postJobEngagementResend` | POST | `jobs/:jobId/engagement/resend` | Resend engagement |
| `createJob` | POST | `jobs` | Create job |

Deprecated aliases: `getEngagementJobsList`, `getEngagementJobDetail`, `updateEngagementJob`, `createJobEngagement` (they call the methods above).

### Legacy job APIs (still present)

| Method | HTTP | Endpoint |
| --- | --- | --- |
| `getJobsListData` | GET | `job/list` + params + `&isMobile=true&appVersion=2` |
| `getAllJobCount` | GET | `job/count` + params + `&isMobile=true&appVersion=2` |
| `getJobInfo` | GET | `job/detail/:jobId?isMobile=true` |
| `updateJobInfo` | PUT | `job/update/:jobId` (adds `isMobileTrue`, `isMobile`) |
| `addJob` | POST | `job/create` |
| `getAllJobInfo` | GET | `job/list/mobile` + param |
| `getOfflineJobList` | GET | `job/list/offline` + params + mobile flags |
| `getRestoredJobs` | GET | `user/job/offline/sync?userId=&...` |
| `updateHasSyncedJob` | PUT | `user/job/sync` |
| `jobLock` | POST | `job/update/locked-data` |
| `resetProduct` | POST | `job/reset/product-edit-flag` |
| `getJobAssignedInstallerName` | GET | `job/task/team-details` + params |
| `jobRebateCalculate` | POST | `job/calculate/product/rebate` |
| `customerAmount` / `getCoPayment` | POST | `job/customer/amount` |
| `smsSentCount` | POST | `job/signature/sms` |

### Tasks / photos (legacy)

| Method | HTTP | Endpoint |
| --- | --- | --- |
| `getTaskInfo` | GET | `task/detail/:jobId` |
| `editSingleTaskPhoto` | PUT | `task/update/single` |
| `editSingleTaskPhotoV2` | PUT | `task/update/single/app2` |
| `retakePhotoUploadForTask` | PUT | `task/discard/photos` |
| `updateDecommissionTaskOption` | PUT | `task/decommission/option` |
| `updateTaskProductList` | PUT | `task/update/equipment-product` |
| `addPhotoLatLong` | POST | `task/add/photoLatLong` |
| `bulkPhotoUrlUpload` | POST | `task/bulk/url-sync` |
| `getCustomerDetail` | GET | `task/customer/details/:jobId` |
| `troubleshootJobPhotos` | POST | `task/sync/by-name` |

Commented in source: `task/detail/app2/:jobId` is disabled.

### Notes

| Method | HTTP | Endpoint |
| --- | --- | --- |
| `getJobNotesListData` | GET | `note/list` + params |
| `getNotesListData` | GET | `notes` + params (`entityType`, `entityId` per comment) |
| `addJobNote` | POST | `notes` |
| `editJobNote` | PATCH | `notes/:noteId` body `{ note }` |
| `deleteJobNote` | DELETE | `notes/:noteId` |

### Sites / events / quotes

| Method | HTTP | Endpoint |
| --- | --- | --- |
| `addSite` | POST | `site/create` |
| `updateSite` | PUT | `site/update?siteId=` |
| `getSiteList` | GET | `company/site/list` + params + mobile flags |
| `getSiteTotalCount` | GET | `company/site/count` + params |
| `getJobListOfSite` | GET | `site/job/list` + params |
| `addJobInSite` | POST | `site/add/job` |
| `getOfflineJobDetails` | GET | `site/job/all-data` + params |
| `getSiteDetails` / `getSiteDetailsById` | GET | `site/detail` / `site/detail?siteId=` |
| `getSiteEvents` | GET | `event/list` + params |
| `updateSiteEvents` | PUT | `event/` + params |
| `addJobFromQuote` | POST | `estimated-quotes/add` |
| `addQuotes` | POST | `quotes/add` |
| `editQuotes` | PUT | `quotes/:quoteId` |
| `getAllQuotesList` | GET | `quotes/list` + param |
| `getQuoteInfo` | GET | `quotes/` + param |
| `getQuoteComments` | GET | `quotes/comment/list` + param |
| `addQuoteComment` | POST | `quotes/comment/add` |
| `deleteQuoteComment` | DELETE | `quotes/comment` + param |

### Calculator / products / rebates

| Method | HTTP | Endpoint |
| --- | --- | --- |
| `getCalculatorTypes` | GET | `calculators/types` |
| `getCalculatorPrefill` | GET | `calculators/prefill` |
| `getCalculatorOriginalEquipment` | GET | `calculators/original-equipment` |
| `postCalculatorEstimate` | POST | `calculators/estimate` |
| `getCalculatorProductBrands` | GET | `products/brands` |
| `getCalculatorProducts` | GET | `products` |
| `getCalculatorBrandModels` | GET | `products/brands/:brand/models` |
| `getBrandList` | GET | `product/brand/list` |
| `getModelNumberList` | GET | `product/model/list` |
| `getPostCodeList` | GET | `postcode/list` |
| `getVEUStatus` / `getProductTypeInformation` | GET | `product/status/list?...` |
| `getProductYesOrNo` | GET | `product/area/size` |
| `getEquipmentList` | GET | `matrix/equipment/list` |
| `addVEECsRebate` | POST | `rebate/calculate?platform=mobile&installerId=` |
| `addSTCRebate` | POST | `rebate/stc/calculate?platform=mobile&installerId=` |
| `addJobRebate` | POST | `rebate/job/total-rebate` |
| `getJobRebate` | GET | `rebate/generate?platform=mobile` |
| `getBrandRebateCount` | POST | `rebate/installation/status` |
| `getCalculateId` | GET | `calculator-usage/id?` |
| `getAddressAutocomplete` | GET | `address/autocomplete?search=` |
| `getAddressDetails` | GET | `address/details?placeId=` |

### Job 13A (glazed)

| Method | HTTP | Endpoint |
| --- | --- | --- |
| `addJob13A` | POST | `glazed/job/create` |
| `job13ARebateCalculate` | POST | `glazed/job/calculate/rebate` |
| `job13ARebateCalculateFromRebateScreen` | POST | `glazed-calculator/generate?installerId=` |
| `allJob13AList` | GET | `glazed/job/list` + params + mobile flags |
| `getAllJob13Count` | GET | `glazed/job/count` + params |
| `getJobAInfo` | GET | `glazed/job/detail/:jobId?isMobile=true` |
| `updateJobAInfo` | PUT | `glazed/job/update/:jobId` |
| `jobAEmailSentCount` | POST | `glazed/send/signature/email` |
| `jobASmsSentCount` | POST | `glazed/job/signature/sms` |
| `getJobATaskInfo` | GET | `glazed-task/detail/:jobId` |
| `updateSingleTaskPhotoForJobA` | PUT | `glazed-task/update/single` |
| `updateTaskAProductList` | PUT | `glazed-task/update/equipment-product` |

### Notifications, CMS, rewards, gallery, chat, config

| Method | HTTP | Endpoint |
| --- | --- | --- |
| `getAllNotification` | GET | `notification` + param |
| `readNotification` | GET | `notification/update-status?notificationId=` |
| `deleteNotification` | DELETE | `notification/:id` |
| `deleteAllNotification` | DELETE | `notification/multi-delete?userId=` |
| `popNotification` | GET | `notification/broadcast/list` |
| `removePopNotification` | GET | `notification/update-status` + param |
| `pushNotificationForMsg` | POST | `notification/message-notification` |
| `syncPhotoNotification` | POST | `notification/sync-photo` |
| `photoSyncAction` | POST | `job-photo-sync-action/create` |
| `getHelp` | GET | `cms?category=help&status=published&...` |
| `getCmsByKey` | GET | `cms/by-key/:key` (`terms_and_conditions`, `privacy_policy`) |
| `getRewardsList` | GET | `reward` + params |
| `getRewardDetails` | GET | `reward/user/:rewardId/:userId` |
| `getOnGoingReward` | GET | `reward/ongoing?currentTime=` |
| `getGalleryJobList` | GET | `photo/installer/job` |
| `addSinglePhotoInGallery` | POST | `photo/add` |
| `getAllJobPhoto` | GET | `photo/list` |
| `addTeamMemberInJobChatChannel` | PUT | `chat/add/member/:channelId` |
| `initChatBot` | POST | `chatbot/chat` |
| `botHistory` | GET | `chatbot/history` |
| `getAppConfig` | GET | `configure/list` |
| `updateRealmLogConfig` | POST | `configure/update` |
| `uploadLogFile` | POST | `configure/upload-logs` | Multipart `apiFiles` / `realmFiles`. Implemented with raw `fetch` and **`Content-Type: multipart/form-data` only — no Bearer header in this method.** |
| `getJobStatusList` | GET | `common/status/list?type=` |
| `getContractorGroupList` | GET | `contractor-groups` |
| `checkCustomer` | GET | `customer/existing/list` |

Endpoints **not invented**: the tables above are the complete set of HTTP paths found on the `API` class in `src/screen/auth/redux/model/api.ts` plus the two extra `fetch` URLs in upload helpers.

---

## 7. Database / Local Storage

### Realm

Singleton: `src/store/RealmService.ts`.

- `schemaVersion: 8`
- Default file path used for log upload: `{DocumentDirectoryPath}/default.realm`
- Migration: only `schemaVersion < 2` sets `SyncJob.photoSyncFailed = false` if missing. **No other migration steps are defined** for versions 3–8.

**Registered schemas** (jobs domain only):

#### `SyncJob` (`SyncJobModal.ts`)

| Field | Type | Notes |
| --- | --- | --- |
| `jobId` | string PK | |
| `isJobUpdate` | bool | Pending metadata sync |
| `photoSyncFailed` | bool | Added in migration from v1 |

#### `JobList`

| Field | Type |
| --- | --- |
| `jobId` | string PK, indexed |
| `_id`, `activityDate`, `companyName`, `customerAddress`, `customerName`, `customerPhoneNumber`, `customerType`, `scheme`, `status`, `siteId` | mixed / optional |

#### `JobDetails`

| Field | Type |
| --- | --- |
| `jobId` | string PK, indexed |
| `data` | mixed (full job payload) |

#### `TaskDetails` (legacy JSON blob)

| Field | Type |
| --- | --- |
| `jobId` | string PK |
| `data` | mixed — **JSON string** of task units/photos |

#### `CustomerDetail`

| Field | Type |
| --- | --- |
| `jobId` | string PK, indexed |
| `data` | mixed |

#### `SiteListItem`

Primary key `_id`. Customer/site fields (`siteName`, `siteNo`, `customer*`, `scheme`, `status`, `jobCount`, etc.) mostly `mixed?`.

#### Structured `NewTaskDetails` family (`NewTaskDetailModal.ts`)

Embedded: `NewTaskPhotoOcrExtracted`, `NewTaskPhotoOcr`, `NewTaskPhoto`, `NewTaskDetailCustomer`, `NewTaskUnit`. Parent `NewTaskDetails` PK `jobId` with unit arrays, signatures, flags, `dataJson` fallback. Photo fields include `localUri`, `url`, `lat`, `long`, OCR, capture metadata.

CRUD helpers: `saveNewTaskDetails`, `getNewTaskDetailData`, `saveTaskDetailDual` in `realmFunctions.js`. Mapper: `newTaskDetailRealmMapper.js`.

#### NSW slim schemas (`NswJobTasksModal.ts`)

| Schema | PK / relation | Important fields |
| --- | --- | --- |
| `NswPhotoSet` (embedded) | — | `id`, `label`, `url`, `localUri`, `lat`/`long`, `address`, `needsSync`, `isCaptured`, `captureDate`, `photoSetType`, … |
| `NswTask` (embedded) | — | `id`, product fields, `photoSets[]`, `unitsJson` |
| `NswJobTasks` | `jobId` | `tasks[]`, `sectionsJson`, `needsPhotoSync`, `updatedAt` |
| `NswJobList` | `jobId` | `jobNumber`, `status`, customer/address, `dataJson`, `updatedAt` |

Helpers (`nswRealmFunctions.ts`): `saveNswJobListItem`, `saveNswJobTasks`, `getNswJobList`, `getNswJobTasks`, `getNswUnsyncedPhotos`, `getAllNswUnsyncedPhotos`, `updateNswPhotoSetLocal`, `markNswPhotoSetUploaded`.

**Relationships:** There are **no Realm object links**. Jobs, tasks, and photos are related by **string `jobId` / `taskId` / photo `id`**. NSW list rows and task documents share `jobId`.

### job13a Realm files (not registered)

`src/screen/job13a/realmModel/` contains `JobListModal`, `JobDetailModal`, `TaskDetailModal`, `SyncJobModal`, `SiteListModal`, `UserRoleModal` (`userRole`: `role`, `accessType`, `sameCompany`). **`RealmService` does not include these schemas.** Using them against the open Realm would fail unless they were previously registered under another name.

### Create / update / query / delete

| Operation | NSW path | Legacy path |
| --- | --- | --- |
| Create/update list | `saveNswJobListItem` | `saveJobList` |
| Create/update tasks | `saveNswJobTasks` | `saveTaskDetails` / `saveNewTaskDetails` |
| Query list | `getNswJobList` | `realm.objects('JobList')` |
| Query tasks | `getNswJobTasks(realm, jobId)` | `objectForPrimaryKey('TaskDetails', jobId)` |
| Photo local update | `updateNswPhotoSetLocal` | mutate JSON in `TaskDetails.data` |
| Photo uploaded | `markNswPhotoSetUploaded` | rewrite URL in JSON; `updateJobSync` |
| Sync queue | `needsSync` on `NswPhotoSet`; `SyncJob.isJobUpdate` | `SyncJob` + URL not containing S3 prefix |

### AsyncStorage

| Key | Purpose |
| --- | --- |
| `accessToken` | Bearer token |
| `refreshToken` | Refresh token |
| `userData` | JSON user |
| `installerData` | JSON company/installer |
| `localPushBackgroundSyncEnabled` | Background photo sync preference |

Language and other keys are written via `saveDataInAsync` from LanguageSelection, profile, job/site/gallery screens (exact extra key names are screen-specific JSON blobs).

### File-based local storage

- Job JSON dumps: `DocumentDirectoryPath/{userId}{jobId}.txt` (`fileStorage.ts`).
- Sync audit logs: `DocumentDirectoryPath/{userId}_{YYYY-MM-DD}.txt` (bottom tab config-driven upload).
- Realm file: `DocumentDirectoryPath/default.realm`.

---

## 8. Image / File Handling

### Capture / select

| Path | Library / function |
| --- | --- |
| Camera stills | `GetCameraImage` in `src/utils/ImagePicker.ts` (`react-native-image-crop-picker` `openCamera`, `includeExif: true`, quality iOS `0.4` / Android `0.7`, **no cropping**) |
| Gallery (cropped) | `GetGalleryImage` / `GetMultipleGalleryImage` (cropping default true, quality `1`) |
| Android system picker | `pickAndroidGalleryAsset` in `galleryPhotos.ts` (`cropping: false`, `includeExif: true`) |
| iOS album browser | `GalleryPickerSheet.tsx` + `CameraRoll.getPhotos` |
| Save to camera roll | `JobDetailScreen` uses `CameraRoll.saveAsset` |
| Documents | `@react-native-documents/picker` in `ImagePicker.ts` |
| Video | `react-native-compressor` `Video.compress`; max **50 MB** in gallery helpers |

Permissions: `react-native-permissions` (camera, photos, location). Android gallery path comments state the system picker does not require `READ_MEDIA_*`.

### Local paths

- Crop-picker returns a temp `path`; callers prefix `file://` when needed.
- Android `content://` URIs are copied to `RNFS.CachesDirectoryPath` before presigned PUT (`presignedUpload.ts`).
- NSW photos store `localUri` on `NswPhotoSet`. Sync resolves the file; missing file → upload fails (`Local file not found`).
- HEIC/HEIF converted to JPEG via `react-native-heic-converter` (`ImagePicker.ts`, `galleryPhotos.ts`).

### Naming conventions

`createImageName` in `src/utils/ImageName.ts`:

```
{jobId}_{taskId}{unitSuffix}{photoSetPrefix}{photoSetId}_{lat}_{long}_{timestamp}.jpeg
```

Unit suffixes: `_E` existing, `_D` decommissioning, `_N` new, `_O` optional extra. Photo set: `P_` (`photoSet`) or `A_` (anything else / after set).

NSW upload fallback name: `task_photo_{photoId}_{Date.now()}.jpg` or `task-photo-{Date.now()}.jpg` in `uploadJobTaskPhoto`.

Customer signature upload (legacy sync): `{jobId}_customerSign_{unix}.png`.

### Upload / sync

1. **NSW primary:** `api.uploadJobTaskPhoto` → `POST jobs/:jobId/tasks/:taskId/photos/:photoId/upload` (Bearer + FormData). Used by `syncSingleNswPhoto` in `backgroundSyncRunner.ts`.
2. **Presigned S3-style:** `PresignedURL` + PUT via XHR (iOS) or `RNFS.uploadFiles` (Android) in `presignedUpload.ts`.
3. **Legacy multipart:** `uploadImage` → `file/upload-media`; `uploadTaskPhoto` → `file/upload-media-with-location` (both raw `fetch`, no Bearer in those helpers).
4. **Direct AWS SDK:** `UploadDocumentFile` in `UploadDocument.ts` uses `react-native-aws3` `RNS3.put` with **hardcoded bucket credentials** (see Security / Technical Debt). Bucket name in code: `1-energy-rebates`, region `ap-southeast-2`.
5. **Binary PUT:** `Api.awsUploadFile`.

A photo is treated as “already on server” in legacy sync if `url` contains:

`https://rebatem8-nsw-dev.s3.ap-southeast-2.amazonaws.com`

(`S3_UPLOADED_URL_PREFIX` in `backgroundSyncRunner.ts`). Local-only photos are those whose URL does **not** include that prefix (`BottomTab.extractAllPhotos`).

### Compression, crop, watermark, OCR, ZIP, S3

| Feature | Identified? |
| --- | --- |
| Compression | Camera JPEG quality; video compress; gallery often quality `1` |
| Cropping | Optional in gallery pickers; camera capture uses `cropping: false` |
| Watermarking | **Not identified in the current codebase** |
| OCR | Google Cloud Vision `images:annotate` from `LocalPhotoList.tsx` using `GoogleVisionKey`. Results stored as `ocrData`. Structured OCR on `NewTaskPhoto.ocrVerification`. UI: `OCRSheetView.tsx` (“M8 AI Feedback”) |
| ZIP | **Not identified in the current codebase** |
| S3 | Presigned URLs, `react-native-aws3`, hardcoded dev bucket URL prefix for “already uploaded” checks |

### Offline image handling

Photos stay on disk (`localUri`) with `needsSync: true` until `uploadJobTaskPhoto` succeeds. Background sync skips photos missing files or missing usable lat/long/address. Auto-sync is disabled while Job Detail is active (`setJobDetailScreenActive`) and until the user enables local-push background sync in profile.

---

## 9. Location

### Libraries

| Library | Usage |
| --- | --- |
| `react-native-background-geolocation` | `getCurrentPosition` on splash (iOS), `TaskDetailScreen`, `JobDetailScreen`, `JobADetailScreen`, quotes screens. `TaskDetailScreen.ensureBackgroundGeolocationReady` sets `desiredAccuracy: DESIRED_ACCURACY_HIGH`. |
| `react-native-geolocation-service` | `getCurrentPosition` on `13AllJobListScreen`, `AllJobListScreen` |
| `react-native-geocoding` | `Geocoder.init(googleMapKey)` then reverse-geocode for photo address |
| `react-native-google-places-autocomplete` | Address entry on quote screens (key passed as `googleMapKey`) |
| Backend `address/autocomplete` + `address/details` | `AddressJobComponent` / engagement address |
| Native `ExifGps` module | Android-only GPS from gallery URI (`NativeExifGps.ts`) |
| EXIF parse | `exifGps.ts` / crop-picker `includeExif` |

`optionForLatLong` (`AppConstant.tsx`): `timeout: 10`, `maximumAge: 0`, `desiredAccuracy: 20`.

### Request / store / attach

1. Splash requests `ACCESS_FINE_LOCATION` (Android alert) or `LOCATION_WHEN_IN_USE` (iOS).
2. Capture time: `BackgroundGeolocation.getCurrentPosition` (or EXIF for gallery).
3. Stored on photo objects: `lat`, `long`, `address` (Realm `NswPhotoSet` / JSON `TaskDetails`).
4. Upload FormData includes `lat`, `long`, `address`.
5. If photo lacks location, sync tries another photo on the same job (`resolvePhotoLocation`); else fails with `Missing photo location for upload`.
6. Reverse geocode via Google Geocoding if address is empty or looks like raw coordinates.

### Background location

- Android permission `ACCESS_BACKGROUND_LOCATION` is declared.
- iOS usage strings cover Always and When In Use; `UIBackgroundModes` includes `fetch` and `remote-notification` (not `location`).
- TransistorSoft license keys are present in `AndroidManifest.xml` and `Info.plist` (values **[REDACTED]**).
- Continuous tracking configuration beyond `ready()` + `getCurrentPosition` is **not identified** as a long-running location listener in JS.

---

## 10. Authentication & Security

### Login flow

1. `LoginScreen` requires network. Submits `{ countryCode, phoneNumber }` to `POST auth/otp/request`.
2. `OtpVerificationScreen` requests FCM permission/token (`FireBaseService.js`), then `POST auth/otp/verify` with `code` + `fcmToken`.
3. Tokens saved (`saveTokensFromAuthResponse`). User persisted; installer `{}` until company select.
4. `CompanyListScreen` `POST auth/select-company`; then `GET auth/me` via `restoreAuthSessionOnLaunch`.
5. Realm opened; navigate to `bottomTab`.

Long-press on Login skips sending OTP and opens OTP screen with `isLongPress: true` (bypass UX for testers). Exact OTP behaviour for that flag is in `OtpVerificationScreen` (not fully enumerated here).

### Token / session storage

- AsyncStorage keys `accessToken`, `refreshToken`, `userData`, `installerData`.
- Axios request interceptor attaches Bearer unless URL is `auth/refresh`.
- On 401: refresh with single-flight `isRefreshing` + waiter queue; `unauthorized` or missing refresh token → `forceAuthLogout`.
- Offline refresh/me failures with `cannot-connect` / `timeout` / `unknown` **keep tokens** and restore cached user/company.
- Logout: `clearAuthTokens`, remove user/installer, `authActions.clearRedux`, reset to `loginScreen`. FCM type `logOutUser` restarts the app (`RNRestart`).

Device headers: `x-platform` (`ios`/`android`), `x-app-version` (`DeviceInfo.getReadableVersion()`), `x-device-id` (`DeviceInfo.getUniqueId()`).

### Environment variables and secrets

**Do not commit or copy real values.** The following **exist in source today** and must be treated as compromised until rotated:

| Location | Kind | Documented as |
| --- | --- | --- |
| `App.tsx` `cred` | Firebase `apiKey` / `appId` / `clientId` | `[REDACTED]` |
| `src/utils/AppConstant.tsx` | Google Maps, Google Vision, chat, SmartLook keys | `[REDACTED]` |
| `src/utils/UploadDocument.ts` | AWS access key + secret | `[REDACTED]` |
| `android/gradle.properties` | Release keystore passwords | `[REDACTED]` |
| `AndroidManifest.xml` / `Info.plist` | TransistorSoft license | `[REDACTED]` |

Firebase config files `android/app/google-services.json` and `ios/GoogleService-Info.plist` are present; contents are not reproduced here.

`react-native-config` is unused; the HTTP base URL is compiled into `api-config.ts`.

---

## 11. Environment Configuration

### Files

| File | Present? |
| --- | --- |
| `.env.staging` | Yes |
| `.env` / `.env.development` / `.env.production` | **Not identified in the current codebase** |
| `ENVFILE=` scripts in `package.json` | **Not identified** (mentioned only in a Cursor rule, not in this `package.json`) |

### `.env.staging` variable names

| Variable | Purpose |
| --- | --- |
| `API_TARGET` | Set to `stage` in the file |
| `BASE_URL` | Staging API origin + `/api/v1/` |

Because nothing imports `react-native-config` `Config`, **these values are not applied at runtime** unless a native build step not found in JS wires them. Runtime API host is `DEFAULT_API_CONFIG.url` in `api-config.ts` (currently the **dev** host).

### Other config constants (`AppConstant.tsx`)

- `pdfUrl` — remote PDF used by `NetInfo.tsx` speed test (`useInternetSpeedMonitor`).
- `TIMEOUT_DURATION` = `60000`.
- `appVersion` from `DeviceInfo.getReadableVersion()`.
- Chat/SmartLook/Maps/Vision keys — see Security (values redacted).

---

## 12. iOS Configuration

| Item | Value / location |
| --- | --- |
| Project | `ios/nsw_rebateM8.xcodeproj` / `.xcworkspace` |
| Display name | `NSW RebateM8` (`Info.plist`) |
| Bundle id | `org.rebatem8.nsw.au.com` |
| Marketing version | `1.0` |
| Build (`CURRENT_PROJECT_VERSION`) | `13` |
| Deployment target | **15.1** (`IPHONEOS_DEPLOYMENT_TARGET`) |
| Architecture | `arm64` required |
| Orientation | Portrait |
| New Architecture | `RCTNewArchEnabled` = true |
| ATS | `NSAllowsArbitraryLoads` false; `NSAllowsLocalNetworking` true |
| Hermes | Enabled in Podfile |
| Modular headers | `use_modular_headers!`; Firebase pods with modular headers |
| `$RNFirebaseAsStaticFramework` | `true` |
| Entitlements file | **Not identified in the current codebase** |

### Podfile (`ios/Podfile`)

- `platform :ios, min_ios_version_supported` (RN helper; Xcode target is 15.1).
- `setup_permissions`: Camera, LocationAccuracy, LocationAlways, LocationWhenInUse, Microphone, PhotoLibrary, Notifications.
- Extra pods: Firebase, RNFBApp, RNFBMessaging, RNCPushNotificationIOS.
- `post_install` → `react_native_post_install` (mac catalyst disabled).

Ruby: `Gemfile` requires Ruby `>= 2.6.10`, CocoaPods `>= 1.13` excluding 1.15.0/1.15.1.

### Permissions (Info.plist usage strings)

- Camera, Photo Library, Photo Library Add
- Location Always, When In Use, Always and When In Use
- Microphone
- Motion (`NSMotionUsageDescription`)

### Background modes

`remote-notification`, `fetch`.

### Firebase

`ios/GoogleService-Info.plist` and root `GoogleService-Info.plist` exist. JS also calls `firebase.initializeApp(cred, { name: 'Rebate M8' })` in `App.tsx` with inline Android-looking client ids.

### Privacy manifest

`ios/nsw_rebateM8/PrivacyInfo.xcprivacy`: accessed API categories File Timestamp, Disk Space, User Defaults, System Boot Time. `NSPrivacyTracking` false. Collected data types array empty.

### Signing

Provisioning profiles / team IDs: **Not identified in the current codebase** (not committed in inspected files). Signing is expected via Xcode.

---

## 13. Android Configuration

From `android/build.gradle` and `android/app/build.gradle`:

| Item | Value |
| --- | --- |
| `compileSdk` | 36 |
| `targetSdk` | 36 |
| `minSdk` | 24 |
| `buildToolsVersion` | 36.0.0 |
| NDK | 27.1.12297006 |
| Kotlin | 2.3.0 |
| Gradle wrapper | **9.0.0** (`gradle-wrapper.properties`) |
| Android Gradle Plugin | Version not pinned in `build.gradle` (`classpath("com.android.tools.build:gradle")` without version) |
| Java / `sourceCompatibility` | **Not identified in the current codebase** |
| Namespace / applicationId | `com.nsw_rebatem8` |
| `versionCode` / `versionName` | `1` / `"1.0"` |
| `multiDexEnabled` | true |
| Hermes | true |
| New Architecture | true (`gradle.properties`) |
| Architectures | `armeabi-v7a,arm64-v8a,x86,x86_64` |
| Edge-to-edge | false |
| Proguard (release) | **disabled** (`enableProguardInReleaseBuilds = false`) |
| Product flavors | **Not identified** (no `productFlavors` block) |
| Build types | `debug`, `release` |
| Google services | Plugin `com.google.gms.google-services` + `google-services:4.4.4` |
| `usesCleartextTraffic` | Manifest uses `${usesCleartextTraffic}` (value supplied by RN/Gradle; not hardcoded in the inspected manifest) |
| Portrait | `android:screenOrientation="portrait"` |
| `allowBackup` | false (`tools:replace`) |

### Signing

- Debug: default `debug.keystore` / `android` passwords (standard RN debug keystore).
- Release: `MYAPP_STORE_FILE=rebatem8-release.keystore`, alias `rebatem8-release`. Store/key passwords live in `gradle.properties` — **[REDACTED]**. Keystore file `android/app/rebatem8-release.keystore` is in the tree (`.gitignore` does not ignore `*.keystore` except a commented line).

### Permissions (`AndroidManifest.xml`)

- `INTERNET`
- `CAMERA` (camera hardware optional)
- `RECORD_AUDIO`
- `POST_NOTIFICATIONS`
- `ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION`, `ACCESS_MEDIA_LOCATION`, `ACCESS_BACKGROUND_LOCATION`

### Native modules

- `MainApplication.kt` — default RN host + `LocalPushNotificationPackage`
- `MainActivity.kt` — component name `nsw_rebateM8`, Fabric enabled
- `LocalPushNotificationModule.kt` — local notifications for offline photo sync

### Firebase

`android/app/google-services.json` present. `missingDimensionStrategy 'react-native-camera', 'general'` remains in `defaultConfig`.

Repositories also include TransistorSoft maven dirs for background-geolocation / background-fetch, plus `jcenter.bintray.com`.

---

## 14. Third-Party Services

| Service | Integration |
| --- | --- |
| **Firebase Cloud Messaging** | `@react-native-firebase/app` + `messaging`. Init in `App.tsx`. Token via `FireBaseService.js`. Background handler in `index.js` (empty body). Foreground in-app popup (`react-native-push-notification-popup`). Types handled: `logOutUser`, `permissionChange`, `syncPhotos`, job/reward/chat types. |
| **Firebase project** | Name in JS: `nsw-rebatem8`. Native google-services files present. Crashlytics package **not** in `package.json`. |
| **AWS / S3** | (1) Presigned URLs from `storage/presigned-url`. (2) `react-native-aws3` with hardcoded keys in `UploadDocument.ts`. (3) Hardcoded **dev** bucket URL prefix for “uploaded” detection. Region seen: `ap-southeast-2`. |
| **Google Maps / Geocoding / Places** | `googleMapKey` in `AppConstant.tsx`; Geocoder + Places Autocomplete + REST geocode in list item components. |
| **Google Cloud Vision** | OCR in `LocalPhotoList.tsx` (`vision.googleapis.com/v1/images:annotate`). |
| **Google Places (backend)** | `GET address/autocomplete` and `address/details` (server-side key not in the app). |
| **Background Geolocation** | TransistorSoft `react-native-background-geolocation` + license metadata. |
| **Background Fetch** | `react-native-background-fetch` (60 minute minimum interval, headless, start on boot). |
| **CodePush / App Center** | **Not identified** |
| **Ant Media** | **Not identified** |
| **GetStream / SmartLook** | Keys defined, **no imports/usages** found |
| **Version check** | `react-native-version-check` on some site/13A list screens |
| **In-app browser** | Dependency present; usage not fully traced in this pass |

---

## 15. Important Business Logic

### A. Session bootstrap (Splash)

File: `src/screen/splashScreen/SplashScreen.tsx` + `restoreAuthSessionOnLaunch`.

1. Request camera / location / (iOS) photos.
2. iOS: one `BackgroundGeolocation.getCurrentPosition`.
3. Restore tokens → `auth/me` or offline cache.
4. If no `company.installerId` → company list.
5. Open Realm, store on Redux, call `updateSiteEvents`.
6. Register FCM open/initial handlers.
7. Navigate to Jobs tab or handle notification type.

### B. Create / edit job (NSW engagement)

Files: `AddJobScreen.tsx`, `EngagementStep.tsx`, `ProductsStep.tsx`, `TeamStep.tsx`, `engagementFormHelpers.ts`.

Stepper keys: **Engagement → Products → Team**.

1. Build form (`createDefaultEngagementForm` / load existing job).
2. Validate engagement fields; `POST jobs` (`createJob`) or `PATCH jobs/:id` (`updateJob`).
3. Products: catalog from rebate calculator Redux; `PATCH jobs/:id/tasks` (`postJobTask`) per product (add/edit/delete). Payload built at the call site (brand, model, serial, install type, etc.).
4. Site assessment: `POST jobs/:id/site-assessment` when unlocked (`isGoodToGoStatus` / post-engagement flags).
5. Resend engagement SMS/email: `postJobEngagementResend`.
6. Locking: `isEngagementLocked` disables edits after certain statuses.

`ComingSoonStep.tsx` and older `StepOne`–`StepFour` / `PhotoStepper` remain in the jobs folder (legacy stepper).

### C. Job list + offline pack

File: `src/screen/home/JobListScreen.tsx`.

1. Online: dispatch `jobList` saga → `GET jobs`.
2. After load, `packJobsToRealm`: always save slim list rows; for jobs missing `NswJobTasks`, `GET jobs/:id/tasks` and `saveNswJobTasks`.
3. Offline: `getNswJobList(realm)` + local search.
4. Opening a job: NSW UI uses `homeTaskDetailScreen` (`TaskDetailScreen`).

### D. Task photos (NSW)

File: `src/screen/home/TaskDetailScreen.tsx`.

1. Load tasks from API if online, else Realm.
2. Capture/select photo; write GPS + `localUri` + `needsSync` via `updateNswPhotoSetLocal`.
3. Upload immediately if online (`uploadJobTaskPhoto`); else wait for background sync.
4. `setJobDetailScreenActive(true)` while on this screen so auto-sync does not fight the user.

### E. Legacy job detail / 13A

- `JobDetailScreen.tsx` — large legacy UI (CameraRoll save, BackgroundGeolocation, older task JSON).
- `job13a/` — glazed jobs using `glazed/*` APIs and `SyncJobFunctions.js` parallel to jobs.

### F. Rebate calculator

Wired screen: `src/screen/RebateCalculator/RebateCalculatorScreen.tsx` + `RebateCalculatorRedux.ts` (`calculators/*`, `products/*`, `postCalculatorEstimate`).

Older: `src/screen/calculator/RebateCalculatorScreen.tsx` + `rebateRedux.ts` (VEEC/STC style `rebate/calculate` APIs). Both reducers are in the store.

### G. Team and company

- Team: installer member CRUD under `installers/:id/members`.
- Company: `EditCompany.tsx` uses installer GET/PUT, file upload, bank-change request.
- Profile drawer menus: `ProfileArrayData.tsx` (many historical items commented out).

### H. Config-driven diagnostics

On bottom-tab focus, `GET configure/list`. If `isApiLog` / `isRealmLog`, uploads daily `{userId}_{date}.txt` and/or `default.realm` to `configure/upload-logs`, then may `POST configure/update` to turn off realm logging.

### I. Roles

Installer admin vs others: tab set and profile menu. Permissions strings may exist on `company` from `auth/me`; enforcement is mostly UI-level (`permissionMessage` constant). A full permission matrix is **not identified** as a single module.

---

## 16. Offline / Sync Architecture

### How offline data is stored

1. **Session:** last `userData` / `installerData` + tokens in AsyncStorage.
2. **Jobs:** `NswJobList` + `NswJobTasks` (and legacy `JobList` / `JobDetails` / `TaskDetails` / `SyncJob`).
3. **Photos:** files on disk; Realm `localUri` + `needsSync`.
4. **Optional:** `{userId}{jobId}.txt` JSON files.

### Connectivity detection

- `NetInfo.addEventListener` in `BottomTab`, `LoginScreen`, `backgroundSync.ts`.
- `useNetworkHandler` (`useNetInfo.ts`) treats “online” as connected **and** reachable **and** (wifi **or** cellular 4g/5g).
- Splash uses API `kind === 'cannot-connect'` to show offline UI and still enter the app from cache.

### When the device goes offline

- Bottom bar: “You are offline!”.
- Job list reads Realm; packing HTTP is skipped.
- Photo captures remain local (`needsSync`).
- Login is blocked (`No Internet Connection!`).
- Token refresh failures that are network-related do **not** log the user out.

### When connectivity returns

`backgroundSync.ts`:

- NetInfo false→true, **debounced 8s**, runs sync (`netinfo-reconnect`).
- App returns to `active`, **debounced 2s** (`app-open`).
- Foreground interval **1 hour**.
- OS BackgroundFetch **minimum 60 minutes**, `stopOnTerminate: false`, `startOnBoot: true`, `enableHeadless: true`, `NETWORK_TYPE_ANY`.
- Cooldown **90s** between automatic runs (`SYNC_COOLDOWN_MS`).
- Headless: `runBackgroundSyncHeadless` in `index.js` opens Realm and runs photo + job sync with `force: true`.

Preference `localPushBackgroundSyncEnabled` (default **false** until enabled on `ProfileDrawerScreen` via `onToggleLocalPushSync`): if false, auto photo sync is skipped (`shouldSkipAutoPhotoSync`).

### Pending uploads / queues

- NSW: `getAllNswUnsyncedPhotos` / per-job `getNswUnsyncedPhotos`.
- Legacy: photos whose URL lacks the hardcoded S3 prefix; `SyncJob.isJobUpdate`; `runPendingJobsBackgroundSync` / `syncSingleJobInBackground`.
- Locks: `nswPhotoSyncLock`, `globalSyncLock`.
- Per-upload timeout **7000 ms** (`uploadWithTimeout`).
- Local notifications (when allowed and app not active): “Uploading x of y…” then success/partial failure. Android uses `LocalPushNotification` native module; iOS uses `PushNotificationIOS`.

After NSW upload success: `markNswPhotoSetUploaded`. Failures increment `failed` and can set `photoSyncFailed` on legacy `SyncJob`.

Bottom tab also POSTs `notification/sync-photo` with per-job local photo counts (online only).

### Retry / errors

- Automatic retries via timers/fetch/reconnect, not a persisted durable queue with backoff multipliers (beyond cooldown + next interval).
- Missing file or missing GPS/address → that photo fails that pass; others continue.
- 401 with expired access token → refresh; persistent unauthorized → logout.

### Race conditions / data-loss risks (current implementation)

1. **Three photo models** (`TaskDetails` JSON, `NewTaskDetails`, `NswJobTasks`) can diverge; packing NSW tasks does not obviously migrate legacy JSON.
2. **Hardcoded S3 prefix** (`rebatem8-nsw-dev`) means stage/prod URLs may still look “unuploaded” and be re-counted/re-uploaded.
3. **Job Detail active skip:** photos captured then left unsynced until the user leaves the screen **and** background sync is enabled.
4. **Default sync off:** `localPushBackgroundSyncEnabled` starts false — photos wait until the profile toggle (or manual upload).
5. **`SyncJobFunctions.syncJobDetails`** does `JSON.parse(taskDetail)` on a Realm object (not a string) — likely runtime failure if that path runs.
6. **`forEach` + `async`** in the same file does not await decommission updates.
7. **Pack vs sync:** `saveNswJobTasks` merges existing `needsSync` / `localUri` fields onto matching photo ids when re-packing from the API. Local captures whose ids are **not** in the server task payload are not reattached.
8. **Headless vs UI** both open `RealmService.getInstance()`; Realm is generally thread-sensitive — concurrent writes are a risk if JS and headless overlap.
9. **`uploadLogFile` / `uploadImage` without Bearer** can fail silently or upload unauthenticated.
10. **Cooldown** can skip a reconnect sync if another trigger ran in the last 90 seconds.

---

## 17. Build & Run Instructions

Prerequisites: Node **≥ 22.11.0**, Yarn, JDK/Android SDK, Xcode (iOS), CocoaPods via Bundler.

### Dependencies

```sh
yarn install
```

`postinstall` runs `patch-package`.

### Environment

There is **no** `ENVFILE=` script. To point the app at a host, change `BASE_URL` in `src/sharedUtils/services/api/api-config.ts` (dev is currently uncommented). `.env.staging` is **not** wired in JS.

### Metro

```sh
yarn start
```

### Android (development)

```sh
yarn android
```

Equivalent: `react-native run-android`.

Release (from `android/`):

```sh
./gradlew assembleRelease
```

Signing uses `gradle.properties` `MYAPP_*` and `android/app/rebatem8-release.keystore`.

### iOS

```sh
bundle install
cd ios && bundle exec pod install && cd ..
yarn ios
```

Open `ios/nsw_rebateM8.xcworkspace` for device/signing.

### Tests / lint

```sh
yarn test
yarn lint
```

ESLint config file at repo root: **Not identified** (script still calls `eslint .`; `@react-native/eslint-config` is a devDependency).

### Firebase / maps

Place valid `google-services.json` / `GoogleService-Info.plist` (already in tree). Google Maps/Vision keys are currently hardcoded in `AppConstant.tsx`.

---

## 18. Common Issues / Troubleshooting

| Symptom | Likely cause (from this project) | What to check |
| --- | --- | --- |
| API hits the wrong environment | Base URL hardcoded to **nswdev** | `src/sharedUtils/services/api/api-config.ts`. `.env.staging` will not change it. |
| `react-native-config` “not working” | Package installed, **never imported** | Use `api-config.ts` or wire `Config` yourself. |
| Login always “No Internet” | Login requires `NetInfo.isConnected` | Simulator network / NetInfo. |
| Session bounce to login offline | No cached `userData` | Need a previous successful `auth/me`. |
| Photos never auto-upload | Sync pref default false; Job Detail skip; missing GPS | Profile local-push toggle; leave task screen; location permission. |
| iOS pod / Firebase header errors | Modular headers + static Firebase flags | Follow current `Podfile`; clean `Pods` + `pod install`. |
| Android background geo build | Extra maven repos for TransistorSoft | `android/build.gradle` `allprojects.repositories`. |
| Duplicate Redux inject warnings | Static slices **and** `useInjectReducer` | Expected in current screens; usually harmless. |
| New Architecture / Reanimated | RN 0.84 + `react-native-worklets/plugin` | Keep Babel plugin last as in `babel.config.js`. |
| Realm schema errors after pull | `schemaVersion: 8` with incomplete migrations | Uninstall app or bump version + write migrations. |
| 13A Realm crashes | job13a schemas not in `RealmService` | Do not open those schema names on the current Realm. |
| Notification to chat does nothing | `messageListScreen` not registered | `App.tsx` vs `navigator/index.tsx`. |
| Release install fails | Keystore passwords / missing `rebatem8-release.keystore` | `android/gradle.properties`, `android/app/`. |
| Google Places / geocode fail | Key restrictions or invalid key | `AppConstant.tsx` `googleMapKey` (rotate if leaked). |
| OCR fail | Vision key / network | `LocalPhotoList.tsx` Vision URL. |
| `jcenter.bintray.com` | Deprecated repo still listed | May fail if JCenter is down; used for background-geo related resolution. |

---

## 19. Important Files

| File | Why it matters |
| --- | --- |
| `App.tsx` | Providers, FCM UI, notification navigation |
| `index.js` | App registry, FCM background, BackgroundFetch headless |
| `src/store/store.ts` | Redux + saga + logout reset |
| `src/store/rootReducer.ts` / `rootSaga.ts` | Domain registration |
| `src/store/RealmService.ts` | Realm schema set and version |
| `src/sharedUtils/services/api/api-config.ts` | **Runtime API host** |
| `src/sharedUtils/services/api/api.ts` | HTTP verbs |
| `src/screen/auth/redux/model/api.ts` | Every REST method + token interceptors |
| `src/screen/auth/redux/AuthRedux.ts` | Session restore, OTP apply, logout |
| `src/screen/navigator/index.tsx` | Full stack map |
| `src/screen/navigator/BottomTab.tsx` | Tabs, offline banner, log upload, photo badge, background sync hook |
| `src/screen/splashScreen/SplashScreen.tsx` | Cold start |
| `src/screen/home/JobListScreen.tsx` | NSW list + Realm packing |
| `src/screen/home/TaskDetailScreen.tsx` | NSW photo capture / upload |
| `src/screen/home/redux/jobsRedux.ts` | Jobs list + photos sagas |
| `src/screen/jobs/AddJob/AddJobScreen.tsx` | Create/edit job stepper |
| `src/screen/jobs/AddJob/engagementFormHelpers.ts` | Validation and job payloads |
| `src/screen/jobs/realmModel/NswJobTasksModal.ts` | Offline NSW schemas |
| `src/screen/jobs/realmModel/nswRealmFunctions.ts` | NSW Realm CRUD |
| `src/services/backgroundSync.ts` | When sync runs |
| `src/services/backgroundSyncRunner.ts` | How photos/jobs upload |
| `src/utils/presignedUpload.ts` | Presigned PUT |
| `src/utils/ImagePicker.ts` | Camera/gallery |
| `src/utils/AppConstant.tsx` | Keys and location options (secrets present) |
| `android/app/build.gradle` / `android/build.gradle` | SDK versions, signing |
| `ios/Podfile` / `ios/nsw_rebateM8/Info.plist` | Pods and permissions |
| `src/assets/index.js` | Image/SVG catalog |
| `src/Translator/i18n.js` | English/Chinese strings |

---

## 20. Developer Onboarding

Recommended order for a new developer:

1. **Run the app** — Node 22+, `yarn install`, Metro, iOS pods or Android emulator ([§17](#17-build--run-instructions)). Confirm the API host in `api-config.ts`.
2. **Auth path** — Read `LoginScreen` → `OtpVerificationScreen` → `CompanyListScreen` → `AuthRedux.restoreAuthSessionOnLaunch` → interceptors in `model/api.ts`.
3. **Navigation** — `src/screen/navigator/index.tsx` then `BottomTab.tsx` (admin vs user tabs).
4. **NSW job happy path** — `JobListScreen` packing → `TaskDetailScreen` photos → `nswRealmFunctions` → `uploadJobTaskPhoto`.
5. **Add Job** — `AddJobScreen` + `engagementFormHelpers` + `postJobTask`.
6. **Offline** — `backgroundSync.ts` constants and `backgroundSyncRunner.ts` locks/upload. Toggle background sync in profile and test airplane mode.
7. **Redux map** — `rootReducer.ts` / `rootSaga.ts`; know that many screens call `api` directly.
8. **Legacy vs NSW vs 13A** — do not mix `job/list` JSON tasks with `NswJobTasks` or glazed `job13a` APIs without checking which screen you are in.
9. **Native** — permissions in Info.plist / AndroidManifest; Firebase files; location license metadata.
10. **Do not copy secrets** from `AppConstant.tsx`, `UploadDocument.ts`, `App.tsx`, or `gradle.properties` into docs or new files; rotate them if this repo is shared.

---

## 21. Known Technical Debt / Risks

- **Secrets in source** (`AppConstant.tsx`, `UploadDocument.ts`, `App.tsx` Firebase `cred`, `gradle.properties` keystore passwords, TransistorSoft licenses). Rotate and move to a secrets manager / CI.
- **`react-native-config` unused**; env files do not drive the API host.
- **Dual/triple job implementations:** NSW (`jobs`, `NswJob*`), legacy (`job/*`, `TaskDetails`), 13A (`glazed/*`) plus unused/commented profile routes.
- **Duplicate calculators** (`calculator/` vs `RebateCalculator/`).
- **job13a Realm models not registered** in `RealmService`.
- **Incomplete Realm migrations** for schemaVersion 8.
- **Hardcoded S3 dev URL** for “already uploaded” detection.
- **Unauthenticated `fetch` uploads** (`UploadImage.ts`, `UploadTaskPhotos.tsx`, `uploadLogFile`).
- **AWS long-lived keys** in `UploadDocument.ts` (client-side secret).
- **`messageListScreen` / `socketClient`** referenced but chat SDK/screen not in the navigator.
- **`sharedUtils/slices` leftover** (`globalSlice` imports missing `src/utils/@reduxjs/toolkit`).
- **`BottomTabLegacy.tsx`**, `dummy.js`, commented Podfile block, commented 13A `getTaskInfoV2`.
- **redux-injectors duplication** of static reducers.
- **Route names are magic strings**; `NavigationScreen` / Cursor `AppScreen` pattern not used.
- **`JSON.parse` on Realm object** in `SyncJobFunctions.js`.
- **Login long-press OTP skip** is a security-sensitive tester path.
- **Release keystore committed** (or at least present in the workspace); `.gitignore` does not ignore keystores.
- **JCenter** still listed in Android repositories.
- **SmartLook / chat keys** unused but committed.
- **i18n init is not on the app root.** Only `src/screen/auth/LanguageSelection.tsx` imports `src/Translator/i18n.js`. `App.tsx` / `index.js` / `SplashScreen` do not. First launch goes to `splashScreen`, so translations may be uninitialized until that import runs.

---

*Generated from the repository as of the inspection date. Do not treat this file as a substitute for reading the cited source files before changing behaviour.*
