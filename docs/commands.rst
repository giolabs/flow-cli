Command Reference
=================

Complete reference for all Flow CLI commands.

flow
----

🚀 Flow CLI - A beautiful, interactive CLI tool for Flutter developers

Build amazing Flutter apps with ease using our comprehensive set of tools for Android, iOS, and multi-flavor development.

**Usage:**

.. code-block:: bash

   flow [OPTIONS] COMMAND [ARGS]...

**Options:**

- ``--version``: Show version information
- ``--verbose, -v``: Enable verbose output
- ``--help``: Show this message and exit

Commands
--------

doctor
~~~~~~

🩺 Check development environment health

Comprehensive health check for Flutter development environment including Flutter SDK, Android SDK, iOS tools, and other dependencies.

**Usage:**

.. code-block:: bash

   flow doctor [OPTIONS]

**Options:**

- ``--fix``: Attempt to fix detected issues automatically
- ``--json``: Output results in JSON format
- ``--verbose``: Show detailed information about each check

analyze
~~~~~~~

📊 Analyze Flutter project for issues

Static analysis and linting for Flutter projects with detailed reporting and actionable recommendations.

**Usage:**

.. code-block:: bash

   flow analyze [OPTIONS]

**Options:**

- ``--path``: Specific path to analyze (default: current directory)
- ``--json``: Output results in JSON format
- ``--fix``: Attempt to fix issues automatically

android
~~~~~~~

🤖 Android development tools

Complete Android development workflow including building, running, device management, and multi-flavor support.

**Usage:**

.. code-block:: bash

   flow android [OPTIONS] COMMAND [ARGS]...

android build
^^^^^^^^^^^^^

Build Android application

**Usage:**

.. code-block:: bash

   flow android build [OPTIONS] [FLAVOR]

**Options:**

- ``--flavor``: Build flavor (development, production, etc.)
- ``--output-format``: Output format (apk, aab)
- ``--target-platform``: Target platform (android-arm, android-arm64)
- ``--release``: Build in release mode
- ``--debug``: Build in debug mode

android run
^^^^^^^^^^^

Run Android application

**Usage:**

.. code-block:: bash

   flow android run [OPTIONS] [FLAVOR]

**Options:**

- ``--device``: Target device ID
- ``--flavor``: Run flavor
- ``--hot-reload``: Enable hot reload

android devices
^^^^^^^^^^^^^^^

List available Android devices

**Usage:**

.. code-block:: bash

   flow android devices [OPTIONS]

**Options:**

- ``--json``: Output in JSON format

android install
^^^^^^^^^^^^^^^

Install APK on device

**Usage:**

.. code-block:: bash

   flow android install [OPTIONS] [APK_PATH]

**Options:**

- ``--device``: Target device ID
- ``--flavor``: Install specific flavor

ios
~~~

🍎 iOS development tools (macOS only)

iOS development tools including simulators, building, and deployment.

**Usage:**

.. code-block:: bash

   flow ios [OPTIONS] COMMAND [ARGS]...

ios devices
^^^^^^^^^^^

List available iOS devices and simulators

**Usage:**

.. code-block:: bash

   flow ios devices [OPTIONS]

**Options:**

- ``--json``: Output in JSON format

ios run
^^^^^^^

Run iOS application

**Usage:**

.. code-block:: bash

   flow ios run [OPTIONS] [FLAVOR]

**Options:**

- ``--device``: Target device/simulator
- ``--flavor``: Run flavor

generate
~~~~~~~~

🎨 Asset generation tools

Automated generation of app icons, splash screens, and other assets with multi-flavor support.

**Usage:**

.. code-block:: bash

   flow generate [OPTIONS] COMMAND [ARGS]...

generate icons
^^^^^^^^^^^^^^

Generate app icons

**Usage:**

.. code-block:: bash

   flow generate icons [OPTIONS]

**Options:**

- ``--source``: Source icon image path
- ``--flavor``: Generate for specific flavor
- ``--platforms``: Target platforms (android, ios)
- ``--adaptive``: Generate adaptive icons (Android)
- ``--force``: Force regeneration

generate splash
^^^^^^^^^^^^^^^

Generate splash screens

**Usage:**

.. code-block:: bash

   flow generate splash [OPTIONS]

**Options:**

- ``--image``: Splash screen image
- ``--background-color``: Background color
- ``--flavor``: Generate for specific flavor
- ``--android-12``: Generate Android 12+ splash screen
- ``--force``: Force regeneration

deployment
~~~~~~~~~~

🚀 Deployment and release tools

Comprehensive deployment solution with Fastlane integration for automated releases to Google Play Store and Apple App Store.

**Usage:**

.. code-block:: bash

   flow deployment [OPTIONS] COMMAND [ARGS]...

deployment setup
^^^^^^^^^^^^^^^^

⚙️ Configure Fastlane for Flutter project

Sets up Fastlane with Flutter-specific configuration for automated deployment.

**Usage:**

.. code-block:: bash

   flow deployment setup [OPTIONS]

**Options:**

- ``--force``: Force setup even if Fastlane already exists
- ``--skip-branch``: Skip creating feature branch

deployment keystore
^^^^^^^^^^^^^^^^^^^

🔐 Generate signing certificates for Android and iOS

Creates keystores and certificates needed for release builds and store deployment.

**Usage:**

.. code-block:: bash

   flow deployment keystore [OPTIONS]

**Options:**

- ``--platform``: Platform to generate keystore for (android, ios, both)
- ``--force``: Force regeneration of existing keystores
- ``--output-dir``: Custom output directory for keystores

deployment release
^^^^^^^^^^^^^^^^^^

📦 Build and deploy releases to app stores

Comprehensive release management with automated building, testing, and deployment.

**Usage:**

.. code-block:: bash

   flow deployment release [OPTIONS]

**Options:**

- ``--platform``: Platform to release (android, ios, both)
- ``--flavor``: Flavor to build
- ``--track``: Release track (internal, alpha, beta, production)
- ``--build-only``: Only build, do not deploy
- ``--skip-tests``: Skip running tests before build

config
~~~~~~

⚙️ Manage Flow CLI global configuration

Configure Flutter SDK paths, default settings, and preferences with interactive setup wizard.

**Usage:**

.. code-block:: bash

   flow config [OPTIONS]

**Options:**

- ``--set``: Set configuration value (key=value)
- ``--get``: Get configuration value
- ``--list``: List all configuration
- ``--init``: Initialize configuration with setup wizard
- ``--reset``: Reset configuration to defaults

Global Options
--------------

All commands support these global options:

- ``--verbose, -v``: Enable verbose output for detailed logging
- ``--help``: Show help message for the command
- ``--version``: Show Flow CLI version (root command only)

Configuration
-------------

Flow CLI stores configuration in ``~/.flow-cli/config.yaml``. Key configuration options include:

- **flutter.sdk_path**: Path to Flutter SDK
- **android.sdk_path**: Path to Android SDK
- **ios.xcode_path**: Path to Xcode (macOS only)
- **general.default_flavor**: Default flavor for builds
- **general.auto_pub_get**: Automatically run ``flutter pub get``

Examples
--------

.. code-block:: bash

   # Check environment
   flow doctor

   # Build Android release
   flow android build production --release

   # Generate icons for all flavors
   flow generate icons --platforms android,ios

   # Setup deployment
   flow deployment setup
   flow deployment keystore
   flow deployment release --track internal

   # Configure Flow CLI
   flow config --init