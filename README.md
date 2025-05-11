# lr-mig2
Lightroom file tidy repo

## Lightroom file management utility

The overall goal is to rationalise a number of lightroom libraries (currently 2) and a number of backup directories created over several years and several re-organisations of files. this involves identify duplicate photography files and directories and remove these from storage in a controlled manner. Identifying files and folders that are not in either of the current lightroom libraries and also identifying folders that have been included in the wrong library e.g. a perosnal photograhy folder that is in the work library.   
The utility will be packaged into a docker container and run in the target machine requiring docker only. 
The utility will be built on a minimal distro for rapid dev/test/ rebuild cycle.

Functioal definitions:
A duplicate file is a file with identical filename, extension and selected exif metadata. The metadata is not always reliable so there may be duplicates with different created dates. This comparison is between files and folders in a current primary location, and a number of backup folders. 
File formats
Files are stored as DNGs for Leica cameras and as the proprietary raw formats for the other cameras used(Sony, Canon), the utility will require exif viewers for each format. Files are also stored as JPEGs but these are often copies generated in lightroom and stored in subdirectories of a directory for a partucular event or job and are often named '3StarQ70' or '_N_StarQxx', the N as a subjective quality indicator for the purpose of curation. These 'Export Directories' (they are generated as an export in lightroom at a specifig jpeg quality) are not to be included in the directory comparison.


## The current state.
* 2 primary Lightroom libraries, one for Personal Photography, one for Work Photography.
* A significant number of file locations where duplicate directories have been made for the purpose of backups or temorary locations while restructuring libraries.


## Processign Approach.
* Scan a set of target directories to build a database of files, their immediate direcotry location, their full path and a limited set of metadata.
* Identify the category of folder (Personal or Work) by the user reviewing a list of dicrecotry names and full paths. The user will rewiew this data in a spreadsheet (category_assignment.csv) and add the tategory as a P or W in the Category field in the spreadsheet.
* The category assignment spreadsheet will be imported into the database and the category type updated in the file database.
* the user will supply the location of the current primary locations for the 2 libraries (Work and Personal). all sub folder in these libraries will be assigned W or P for the Work and Personal libraries respectively.
* the user will review all category asignments to determine if any have been miscategorised
* duplicate directories will be determined by queryign the database. If a folder from a backup location has the exact name, number of files and size then it will be categorised as a 'Folder Duplicate Exact'(excluding and subfolders names NStarQxx). If a backup location has a folder with the same name, all the files that are in the similarly named Primary library folder, but some additional files that are not present in the primary then that backup folder will be categorised 'Folder duplicate plus y%', the y% indicating by file quaity the number of extra files. The opposite to this latter case with fewer files in the backup folder then that should be categorised as a 'Folder Duplicate minus y%'(excluding and subfolders names NStarQxx) and the y% calculated from the perspecive of the current library.


## Impementation
The application will be run in docker. the database should be postgres, the main language for processing data should be python. SQL should be used to define the table structures in the DB. The majority of code will be developed in the Cursor IDE using calude Sonnet 3.7 

## Development management
* Automated tests need to to be developed at each step
* All steges of development will be versioned
* Test data needs to be created to catch edge cases and for each scenario tobe managed
* A list of development tasks must be maintained in DEVELOPMENT_PLAN.md, and when completed marked as such with a version number
* Regular commits with meaningful messages. no more that 1 functional area tobe included in a single commit - mutiple changes are allowed.
* 

## Roadmap
This is the high level plan for developing the application.
1) file scanning and metadata storage
2) Manual categorisation
3) Analytics to determin type of duplicate direcotory, miss allocated directores or unincluded directories (in neither work or personal libraries
4) File and direcotry move functions and auditing
5) Deletion functions with copy to slow storage - recoverable in case of error in initial classification 


