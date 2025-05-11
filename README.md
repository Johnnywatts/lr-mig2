# lr-mig2
Lightroom file tidy repo

## Lightroom file management utility

The overall goal is to identify duplicate photography files and directories and remove these from storage in a controlled manner. 
The utility will be packaged into a docker container and run in the target machine requiring docker only. 
The utility will be built on a minimal distro for rapid dev/test/ rebuild cycle.

Functioal definitions:
A duplicate file is a file with identical filename, extension and selected exif metadata. The metadata is not always reliable so there may be duplicates with different created dates. This comparison is between files and folders in a current primary location, and a 


The current state.
* 2 primary Lightroom libraries, one for Personal Photography, one for Work Photography.
* A significant number of file locations where duplicate directories have been made for the purpose of backups or temorary locations while restructuring libraries.


Processign Approach.
* Scan a set of target directories to build a database of files, their immediate direcotry location, their full path and a limited set of metadata.
* Identify the category of folder (Personal or Work) by the user reviewing a list of dicrecotry names and full paths. The user will rewiew this data in a spreadsheet (category_assignment.csv) and add the tategory as a P or W in the Category field in the spreadsheet.
* The category assignment spreadsheet will be imported into the database and the category type updated in the file database.
* the user will supply the location of the current primary locations for the 2 libraries

