# QDataMap
QDataMap QGIS3 plugin – Release 1.1

## Installation

**Requirements:** QGIS 3.44

1. Download the latest `.zip` from the [Releases](https://github.com/claudioribotta/QDataMap/releases) page.
2. In QGIS, go to **Plugins → Manage and Install Plugins → Install from ZIP**.
3. Select the downloaded `.zip` and click **Install Plugin**.
4. Enable *QDataMap* in the plugin list.

On first run, the plugin will detect and offer to automatically install any missing Python dependencies (`pandas`, `chardet`, `matplotlib`, `seaborn`). 

If auto-install fails, open the QGIS Python console and run:

```
import pip
pip.main(['install', 'pandas', 'chardet', 'matplotlib', 'seaborn'])
```
