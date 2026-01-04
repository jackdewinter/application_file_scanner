# Change Log

## Unversioned - In Main, Not Released

<!-- pyml disable-next-line no-duplicate-heading-->
### Added

- [Import latest code from PyMarkdown project into this project](https://github.com/jackdewinter/application_file_scanner/issues/32)
    - Pulling in latest changes to properly start this repo.
- [Change exclude patterns to use gitignore style exclusions.](https://github.com/jackdewinter/application_file_scanner/issues/33)
    - Asked for feature from [PyMarkdown](https://github.com/jackdewinter/pymarkdown).
- [Add support for gitignore through external calls to git.](https://github.com/jackdewinter/application_file_scanner/issues/38)
    - Asked for feature from [PyMarkdown](https://github.com/jackdewinter/pymarkdown).
- [Add directory level exclusion checking as an option to reduce the load on
      the main exclusion call.](https://github.com/jackdewinter/application_file_scanner/issues/36)
    - Designed to reduce the impact on calling the gitignore API on a per file basis.

<!-- pyml disable-next-line no-duplicate-heading-->
### Changed

- [Add ability to collect statistics on what was scanned and how.](https://github.com/jackdewinter/application_file_scanner/issues/34)
    - Changed during debugging to make understand what is happening more evident.
- [Add more logging to better understand what library is doing.](https://github.com/jackdewinter/application_file_scanner/issues/35)
    - Changed during debugging to make understand what is happening more evident.

<!-- pyml disable-next-line no-duplicate-heading-->
### Fixed

- [Type of pathing returned by calls can be different.](https://github.com/jackdewinter/application_file_scanner/issues/37)
    - Globbed vs unglobbed pathing returned either full or partial pathing.  Unified.

## Version 0.6.0 - Date: 2025-12-25

<!-- pyml disable-next-line no-duplicate-heading-->
### Added

- None

<!-- pyml disable-next-line no-duplicate-heading-->
### Changed

- updated all dependencies to latest version
- updated project to comform with cookieslicer template for libraries
- pulled in latest version of 'application_file_scanner' from PyMarkdown

<!-- pyml disable-next-line no-duplicate-heading-->
### Fixed

- None

## Version 0.5.0 - Date: 2021-05-16

<!-- pyml disable-next-line no-duplicate-heading-->
### Added

- Initial release

<!-- pyml disable-next-line no-duplicate-heading-->
### Changed

- None

<!-- pyml disable-next-line no-duplicate-heading-->
### Fixed

- None
