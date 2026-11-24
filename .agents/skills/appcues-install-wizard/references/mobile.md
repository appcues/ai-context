# Direct Mobile install

Sources: docs.appcues.com/mobile-installation-overview/installing-the-mobile-sdk [OVERVIEW] · /mobile-installation-overview/registering-your-mobile-app-in-studio · /mobile-troubleshooting/using-the-mobile-debugger [DEBUGGER] · SDK repos: github.com/appcues/appcues-ios-sdk (+ DocC at appcues.github.io/appcues-ios-sdk), appcues-android-sdk, appcues-react-native-module, appcues-flutter-plugin, appcues-capacitor-plugin.

Always use the **latest release** of each SDK. Check the repo's Releases page or the package registry (`npm view @appcues/react-native version`, pub.dev, Maven Central) rather than hardcoding a version from this file. If a signature here doesn't compile, read the repo README / source for the installed version.

**Read only the section for the user's platform.**

## Before you start (all platforms)

- **Account ID**: Studio → Settings → Account.
- **Application ID**: register the app in Studio → Settings → **Apps & Installation** → Add App → name + platform → Save. Teams often register one app per environment (dev/prod) to keep data separate, which means a different App ID per build config. If the Appcues MCP is connected, `list_apps` shows the registered apps.
- **URL scheme** `appcues-<APPLICATION_ID>` is **required** for previewing content and for the debugger. Plan for it, don't skip it.
- **EU accounts** need the EU hosts at init: API `https://api.eu.appcues.net`, settings `https://fast.eu.appcues.com`.
- Install sequence [OVERVIEW]: SDK + init → identify (+ group) → screen → track → URL scheme → verify → (later) element targeting for anchored tooltips, Embed frames.
- Store the Account and App IDs in the project's config pattern (xcconfig/Info.plist, `BuildConfig`/gradle properties, `.env` via react-native-config, `--dart-define`, etc.), especially if dev and prod use different App IDs.
- Wrap the SDK in one small service/module (`AppcuesService`, `analytics/appcues.ts`, `appcues_service.dart`) so call sites never touch the SDK directly and failures can't crash the app.

## Rules shared with web (from the plan)

- identify on login **and on cold launch / session restore** when the user is already signed in. Then call group immediately after.
- User ID: the plan's field, as a string, never changing. Don't send a `userId` property.
- Properties: plan names, plan types, no nested objects/arrays, no empty strings (omit instead). Dates as whole-number Unix timestamps or ISO 8601 strings, unless the platform API accepts native date types (check the SDK docs).
- `reset()` on logout. `anonymous()` only if the plan wants pre-login content (MAU impact).
- **Screens**: call `screen("<Title>")` for each meaningful screen. Use human-readable, stable titles, because they're what content targets. Manual screen tracking is preferred over automatic [iOS docs]. If the plan lists screens, use those exact titles.
- **Events**: exact plan names at the success point. If the product also has a web app, same-named events are pooled across platforms. Follow the plan's naming (it may suffix platform-specific names).
- Mobile `track()` events have **no backfill**, and there's no no-code event tracking on mobile.

---

## iOS (Swift)

**Requirements**: renders content on iOS 13+ (iOS 11–12 analytics only).

**Install**, using whichever the project already uses:
- SPM (Xcode → Add Packages, or `Package.swift`):
  ```swift
  .package(url: "https://github.com/appcues/appcues-ios-sdk", from: "5.0.0")
  ```
- CocoaPods: `pod 'Appcues'` then `pod install`.
- XCFramework: download `AppcuesKit.xcframework.zip` from Releases → Embed & Sign.

Editing `project.pbxproj` by hand is fragile. If the project uses SPM through Xcode (not `Package.swift`), give the user the exact Xcode steps and let them add the package. Do the same if `pod install` can't run.

**Init** (`import AppcuesKit`; keep one shared instance):
```swift
let appcuesConfig = Appcues.Config(
    accountID: APPCUES_ACCOUNT_ID,
    applicationID: APPCUES_APPLICATION_ID)
// EU:
//  .apiHost(URL(string: "https://api.eu.appcues.net")!)
//  .settingsHost(URL(string: "https://fast.eu.appcues.com")!)
appcues = Appcues(config: appcuesConfig)
```
Put it in `application(_:didFinishLaunchingWithOptions:)`, or for SwiftUI in the `App` init / a shared service.

**Calls**: `identify(userID:properties:)`, `group(groupID:properties:)`, `track(name:properties:)`, `screen(title:properties:)`, `reset()`, `anonymous()`, `debug()`.
```swift
appcues.identify(userID: user.id, properties: ["createdAt": user.createdAt, "planTier": user.planTier])
appcues.group(groupID: account.id, properties: ["planTier": account.planTier])
appcues.track(name: "Purchased First Plan")
```
Screens:
```swift
override func viewDidAppear(_ animated: Bool) { super.viewDidAppear(animated); appcues.screen(title: "Screen Name") }
// SwiftUI
.onAppear { appcues.screen(title: "Screen Name") }
```
(`trackScreens()` gives automatic UIKit tracking, but manual is preferred.)

**URL scheme**, part 1. Info.plist (merge into existing `CFBundleURLTypes` if present):
```xml
<key>CFBundleURLTypes</key>
<array>
  <dict>
    <key>CFBundleTypeRole</key><string>Editor</string>
    <key>CFBundleURLName</key><string>$(PRODUCT_BUNDLE_IDENTIFIER)</string>
    <key>CFBundleURLSchemes</key>
    <array><string>appcues-APPCUES_APPLICATION_ID</string></array>
  </dict>
</array>
```
Part 2, handle the links:
```swift
// SceneDelegate
func scene(_ scene: UIScene, willConnectTo session: UISceneSession, options connectionOptions: UIScene.ConnectionOptions) {
    let unhandledURLContexts = appcues.filterAndHandle(connectionOptions.urlContexts)
    // handle remaining links
}
func scene(_ scene: UIScene, openURLContexts URLContexts: Set<UIOpenURLContext>) {
    let unhandledURLContexts = appcues.filterAndHandle(URLContexts)
}
// AppDelegate only
func application(_ app: UIApplication, open url: URL, options: [UIApplication.OpenURLOptionsKey: Any] = [:]) -> Bool {
    guard !appcues.didHandleURL(url) else { return true }
    return false
}
// SwiftUI
.onOpenURL { url in guard !appcues.didHandleURL(url) else { return } /* app links */ }
```
Integrate with the app's existing deep-link handler rather than replacing it.

---

## Android (Kotlin)

**Requirements**: compileSdk 35+, minSdk 21+. The SDK uses Jetpack Compose, so apply the `kotlin-android` plugin or use AGP 8.4+. (React Native/Flutter docs ask for AGP 8.6+.)

**Install** (module `build.gradle(.kts)`; `mavenCentral()` in repositories):
```kotlin
implementation("com.appcues:appcues:<latest_version>")
```
Look up the latest version from Maven Central / GitHub Releases. Use the version catalog (`libs.versions.toml`) if the project has one.

**Init** in the `Application` subclass (create one if missing and register it in the manifest. Ask first):
```kotlin
appcues = Appcues(this, APPCUES_ACCOUNT_ID, APPCUES_APPLICATION_ID)
// EU:
// appcues = Appcues(this, APPCUES_ACCOUNT_ID, APPCUES_APPLICATION_ID) {
//     apiBasePath = "https://api.eu.appcues.net"
//     apiSettingsPath = "https://fast.eu.appcues.com"
// }
```
If the app uses DI (Hilt/Koin), provide the instance as a singleton.

**Calls**:
```kotlin
appcues.identify(userId, properties)
appcues.group(groupId, properties)
appcues.track(name, properties)
appcues.screen(title, properties)
appcues.reset()
```
Screens: `appcues.screen("Screen Name")` in `onResume()` (Activities/Fragments), or in a Compose `LaunchedEffect` / navigation destination listener. `trackScreens()` exists for automatic Activity tracking (uses the Activity label).

**URL scheme**. AndroidManifest, on the launcher Activity (add a second intent-filter):
```xml
<intent-filter>
    <data android:scheme="appcues-APPCUES_APPLICATION_ID" />
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
</intent-filter>
```
Handle the intent in that Activity:
```kotlin
override fun onCreate(savedInstanceState: Bundle?) { super.onCreate(savedInstanceState); handleLinkIntent(intent) }
override fun onNewIntent(intent: Intent?) { super.onNewIntent(intent); handleLinkIntent(intent) }
private fun handleLinkIntent(intent: Intent?) {
    if (appcues.onNewIntent(this, intent)) return
    // existing app link handling
}
```

---

## React Native (incl. Expo 50+)

**Requirements**: RN 0.73+ / Expo SDK 50+. Android compileSdk 35+, minSdk 21+, AGP 8.6+ (8.8.2+ recommended; on AGP < 8.8.2 you may need `android.experimental.lint.version = 8.8.2` in `gradle.properties`). iOS 11+ to install, 13+ to render.

**Install**: `npm install --save @appcues/react-native` (or yarn/pnpm per lockfile), then `cd ios && pod install`. **Expo managed**: this needs a dev build or prebuild (`npx expo prebuild`), not Expo Go. Tell the user.

**Init**: await before any other call (async bridge):
```ts
import * as Appcues from '@appcues/react-native';

await Appcues.setup(APPCUES_ACCOUNT_ID, APPCUES_APPLICATION_ID);
// EU:
// await Appcues.setup(ACCOUNT_ID, APP_ID, { apiHost: 'https://api.eu.appcues.net', settingsHost: 'https://fast.eu.appcues.com' });
```
Do this once at app start (root component effect or app bootstrap). The wrapper should hold a `ready` promise that other calls await.

**Calls**:
```ts
Appcues.identify(user.id, { createdAt: toUnixSeconds(user.createdAt) });
Appcues.group(account.id, { planTier: account.planTier });
Appcues.track('Purchased First Plan');
Appcues.screen('Contact List');
Appcues.reset(); // logout
```
(`reset`, `anonymous`, `debug`, `didHandleURL` are exported by the module but not shown in its README. Check `node_modules/@appcues/react-native` types if unsure.)

**Screens with React Navigation**: hook `onStateChange` / `onReady` on `NavigationContainer` and call `Appcues.screen(currentRouteName)` when the route name changes. Use the plan's screen titles if given.

**URL scheme**:
```sh
npx uri-scheme add appcues-APPCUES_APPLICATION_ID --ios
npx uri-scheme add appcues-APPCUES_APPLICATION_ID --android
```
(Expo: add the scheme to `app.json` `expo.scheme`, or add it via a config plugin, then prebuild.) Handle the links:
```ts
import { Linking } from 'react-native';
Linking.addEventListener('url', async ({ url }) => {
  if (await Appcues.didHandleURL(url)) return;
  // existing link handling
});
```
Also check `Linking.getInitialURL()` on cold start if the app already handles that. If the app uses React Navigation `linking` config, integrate there instead of adding a competing listener.

Push for Expo (if the plan asks): `@appcues/expo-config` plugin.

---

## Flutter

**Requirements**: Android compileSdk 35+, minSdk 21+, AGP 8.6+. On AGP 8 you **must** apply `kotlin-android`; on AGP 9+ you **must not**. iOS 11+ install, 13+ render (`platform :ios, '11.0'`+ in Podfile).

**Install**: `flutter pub add appcues_flutter` (or add `appcues_flutter: <latest_version>` to `pubspec.yaml` + `flutter pub get`).

**Init** (in `main()` after `WidgetsFlutterBinding.ensureInitialized()`, or app bootstrap):
```dart
import 'package:appcues_flutter/appcues_flutter.dart';

await Appcues.initialize(APPCUES_ACCOUNT_ID, APPCUES_APPLICATION_ID);
// EU:
// final options = AppcuesOptions()
//   ..apiHost = 'https://api.eu.appcues.net'
//   ..settingsHost = 'https://fast.eu.appcues.com';
// await Appcues.initialize(ACCOUNT_ID, APP_ID, options);
```

**Calls**:
```dart
Appcues.identify(user.id, {'createdAt': user.createdAt.millisecondsSinceEpoch ~/ 1000});
Appcues.group(account.id, {'planTier': account.planTier});
Appcues.track('Purchased First Plan');
Appcues.screen('Contact List');
Appcues.reset(); // logout
```
Screens: a `NavigatorObserver` (`didPush`/`didPop`) or the router's route-change callback (go_router `routerDelegate` listener) calling `Appcues.screen(routeName)`.

**URL scheme**:
- If the app uses Flutter's built-in deep linking with Router, disable automatic handling so Appcues links reach the SDK:
  - iOS Info.plist: `<key>FlutterDeepLinkingEnabled</key><false/>`
  - Android main Activity: `<meta-data android:name="flutter_deeplinking_enabled" android:value="false" />`

  ⚠️ This changes how the app's existing deep links are handled. Explain it and confirm before doing it, and make sure the app's links are routed manually afterward.
- Register the scheme: the iOS `CFBundleURLTypes` block and the Android intent-filter from the sections above.
- Pass the **full** URI (scheme + host) to the SDK first:
  ```dart
  final handled = await Appcues.didHandleURL(uri);
  if (!handled) { /* route normally */ }
  ```
  (Usually via the app's existing link stream, e.g. `app_links` / `uni_links`.)

---

## Ionic / Capacitor

**Requirements** (stricter): latest plugin needs **Capacitor 8** (`@appcues/capacitor@5.0.6` for Capacitor 7), Android compileSdk 36+, minSdk 24+, AGP 8.13+, iOS 15+. Check these before installing.

```sh
npm install @appcues/capacitor
npx cap sync
```
```ts
import { Appcues } from '@appcues/capacitor';
await Appcues.initialize({ accountId: APPCUES_ACCOUNT_ID, applicationId: APPCUES_APPLICATION_ID });
// EU: add config: { apiBasePath: 'https://api.eu.appcues.net', settingsHost: 'https://fast.eu.appcues.com' }

Appcues.identify({ userId: user.id, properties: { planTier: 'standard' } });
Appcues.group({ groupId: account.id, properties: { planTier: 'standard' } });
Appcues.track({ name: 'Purchased First Plan' });
Appcues.screen({ title: 'Contact List' });
Appcues.reset();
```
URL scheme: `npx uri-scheme add appcues-APPCUES_APPLICATION_ID --ios|--android`, then:
```ts
App.addListener('appUrlOpen', (event) => {
  const handled = Appcues.didHandleURL({ url: event.url });
  if (!handled) { /* app links */ }
});
```
(Place it inside `<IonReactRouter>` for Ionic React.) Embeds aren't available on Ionic.

---

## Unsupported platforms

.NET MAUI, Xamarin, Cordova and Unity have no Appcues SDK. Say so plainly, and suggest the user contact their Appcues team about options. Don't improvise a bridge.

---

## Verify (mobile debugger) [DEBUGGER]

Build and run on a simulator or device with the new code, then launch the debugger in one of these ways:
1. Scan the QR code on the app's page in Studio → Settings → Apps & Installation.
2. Open `https://mobilebuilder.appcues.com/?type=debugger&appId=<APP_ID>` on the device.
3. Deep link: iOS sim `xcrun simctl openurl booted "appcues-<APP_ID>://sdk/debugger"`; Android `adb shell am start -a android.intent.action.VIEW -d "appcues-<APP_ID>://sdk/debugger"`; RN `npx uri-scheme open "appcues-<APP_ID>://sdk/debugger" --ios|--android`.
4. Call `appcues.debug()` from a dev-only menu (never expose it to end users).

Check that these rows are green: **Installed SDK** (correct Account and App ID), **Connected to Appcues**, **Appcues Deep Link** (tap to test), **Tracking Screens** (navigate to another screen if it shows "…"), **User Identified** (the plan's user ID), and **Group Identified**. Perform each plan event and watch for it in the debugger's recent events, then in Studio's Events Explorer.

Deep link error codes: **1** = URL scheme not registered (Info.plist / manifest) · **2** = scheme registered but the SDK isn't receiving the link (handler not wired) · **0/3** = retry the test.
