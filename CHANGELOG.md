# [1.3.0](https://github.com/AN0DA/printerm/compare/v1.2.0...v1.3.0) (2025-10-10)


### Bug Fixes

* **cli:** correct template context generation logic in print command ([d4107dc](https://github.com/AN0DA/printerm/commit/d4107dc68fa093f7a05afaa1ec9a5bf38fc3dfe5))
* **cli:** correct variable input handling in print_template function ([6f728f5](https://github.com/AN0DA/printerm/commit/6f728f5f2b92211151b5c373a88f784f6b6dadc0))
* **cli:** refactor update handling and improve type hints ([e867eaf](https://github.com/AN0DA/printerm/commit/e867eaf397aa92475d49abc9227c715959f18955))
* **gui:** improve keyboard shortcut handling in template dialog ([f96f0df](https://github.com/AN0DA/printerm/commit/f96f0dfc67740a70df608685163137a5f309c3d2))
* **update:** improve retry logic and error handling in update checks ([8dfd0d1](https://github.com/AN0DA/printerm/commit/8dfd0d177f0e9f2f9d71cc0c98230d79a329a18d))


### Features

* **gui:** add application icons and update HTML template for favicon ([8b012d6](https://github.com/AN0DA/printerm/commit/8b012d63cc9bcb02b4c53f61255b77da016ffa7c))
* **gui:** add direct printing functionality for templates ([85ddcdd](https://github.com/AN0DA/printerm/commit/85ddcdd663659576b9b7c2c25e274ad1d496eff3))
* **gui:** enhance print template layout and validation feedback ([59512bf](https://github.com/AN0DA/printerm/commit/59512bf19035d51fdbde168fbffcf6c864e73475))
* **gui:** enhance template dialog with print confirmation and reopen option ([7a35964](https://github.com/AN0DA/printerm/commit/7a359649a34ef519b3550d2dfae39d90e0841d86))
* **gui:** enhance template dialog with status feedback and button management ([d7835a2](https://github.com/AN0DA/printerm/commit/d7835a2a4ffa87dcbbae77f5bf2bc8b150a3142d))
* **update:** implement update checking and notification system ([948d89d](https://github.com/AN0DA/printerm/commit/948d89d7a6ce0147105cc561b252dda95980a917))
* **web:** remove preview functionality and use template display name ([0c19566](https://github.com/AN0DA/printerm/commit/0c1956629d39e8e23e8defd166e3aa9246d9dea8))

# [1.2.0](https://github.com/AN0DA/printerm/compare/v1.1.1...v1.2.0) (2025-07-02)


### Bug Fixes

* Re-raise NetworkError without wrapping in get_latest_version method ([79675f2](https://github.com/AN0DA/printerm/commit/79675f24624c9149bc2b7d0bd671bd141c6b4390))
* Template context generation logic in TemplatePreview ([520de2d](https://github.com/AN0DA/printerm/commit/520de2de595bee0abb81faea042ef3716b1e4f1f))
* Update python-escpos dependency extras ([1f6c478](https://github.com/AN0DA/printerm/commit/1f6c4788bcde6f24a5205bdaae4f45b91b8548b2))
* update version fetching to use PyPI and improve error handling ([8c70166](https://github.com/AN0DA/printerm/commit/8c7016649b9fb745bde785cf85a85ffac28d1706))


### Features

* add Dockerfile for application containerization ([c58bdd6](https://github.com/AN0DA/printerm/commit/c58bdd6add2e0402ebd0bdd71699a146e96d33cf))
* Enhance markdown rendering ([3ec1077](https://github.com/AN0DA/printerm/commit/3ec10772520f758e04fa0b53c0c1b8fb9ebff5de))
* Enhance template preview with HTML rendering and styling support ([7115952](https://github.com/AN0DA/printerm/commit/71159520b657b9d7933eb1d63be50cba688b496f))
* Implement template scripts system for dynamic context generation ([84b5456](https://github.com/AN0DA/printerm/commit/84b5456bd2ef29b8479eb3bd6b6308b4cc65458f))
* Improve GUI design and capabilites ([b40e25f](https://github.com/AN0DA/printerm/commit/b40e25fd9663963bda8219f4e60820c0a2cbbaaa))
* Improve web interface UX ([4030ddf](https://github.com/AN0DA/printerm/commit/4030ddffd0f1e353d5374f2696715db7bc1596eb))
* restructure CLI for improved user experience and add template suggestions ([f4a05d5](https://github.com/AN0DA/printerm/commit/f4a05d5d276fb8b9a5241d5b92ef53a89a35751c))
* update dependencies to python-escpos[all] and remove obsolete packages ([826a13b](https://github.com/AN0DA/printerm/commit/826a13b0dac70e54f463b9a0ffa4dfd34921bf4d))

## [1.1.1](https://github.com/AN0DA/printerm/compare/v1.1.0...v1.1.1) (2025-03-21)


### Bug Fixes

* centralize template folder path in config ([30d0711](https://github.com/AN0DA/printerm/commit/30d07115e70c1bd49989b2adf56a664ef571f2e8))
* Update config file path to use platformdirs for user-specific configuration ([77ed66a](https://github.com/AN0DA/printerm/commit/77ed66afab387526364a51dc028528680d64f488))
* Update release configuration to use uvx for version management ([386b020](https://github.com/AN0DA/printerm/commit/386b0203f471400f91c702ffa4685bacdb8d9c16))
* Update Ruff linter check path to use printerm directory ([ed352b9](https://github.com/AN0DA/printerm/commit/ed352b92861fd2f338410df8fa778b5712f05f70))

# [1.1.0](https://github.com/AN0DA/tp/compare/v1.0.0...v1.1.0) (2024-11-10)


### Bug Fixes

* improve error handling in printer and version functions ([fe32b50](https://github.com/AN0DA/tp/commit/fe32b50b005d5ca6dd347d6cc3a962021f8d0e49))


### Features

* add `requests` ([2ed411f](https://github.com/AN0DA/tp/commit/2ed411f806513faef58c79cdb36d8df37112e54c))
* add support for flask port and secret key settings ([82b3e9c](https://github.com/AN0DA/tp/commit/82b3e9cc7073d6de2ba15aae86831b1d6eaa1df2))
* Autoupdate on start ([c6c12e4](https://github.com/AN0DA/tp/commit/c6c12e4ac5e1904451335f2a1e9ae58615197b0a))
* Implement print templates ([9b69c0b](https://github.com/AN0DA/tp/commit/9b69c0bf806fdb31db7d129ff0d1e68226a2520c))





Bumping version from 1.0.0 to 1.1.0

# 1.0.0 (2024-10-28)


### Features

* Add desktop and web GUI; refactor src code structure ([bcc9c7d](https://github.com/AN0DA/tp/commit/bcc9c7d9e0e3a0c15424c03634d79931d8e0ecb7))
* Add PR checks and Sonarlint config ([e0bcd0c](https://github.com/AN0DA/tp/commit/e0bcd0cc4b8bcde5892657dddbf6f4b756c59912))





Bumping version from 0.2.0 to 1.0.0
