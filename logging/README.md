# GARPR LOGGING
This logging module is for developers to easily log issues and messages to a standard output file in Garpr.
This comes in handy when you have a lot of things happening and an error occurs.

### Functions
If you wish to write to the log file you may perform one of the following methods after using
from logging.log import Log

#### Default Logging
- call ```Log.log(string moduleName, string logMessage)```
- This method logs your logMessage w/ moduleName to the default location: logging/garpr.log
- If you don't want to log the module, just put None for the first param.

#### Write to Specific, Non-Default
- instantiate a new instance of ```Log(string dirPath, string fileName)```
- on this new log object (logObject) call the following method:
- ```logObject.log(string message)```
- this will write your message to the log file indicated in your object instantiation