#-----------------------------------------------------------------------------------------
# Generic utility functions used in day today life.
#
#-----------------------------------------------------------------------------------------
import math
import numpy
import os
#import boto3
#import s3fs

# Tertiary operation on NaN.
# If a given numeric variable is NaN, return the second parameter, otherwise return the variable itself
# 
def if_nan(var, val):
    if(var is None):
        return val
    if(math.isnan(var)):
        return val
    
    return var

# Tertiary operation on null strings.
# If a given string variable is None or empty, return the second parameter, otherwise return the string itself
# 
def if_null(var, val):
    if(var is None):
        return val
    if(var == ""):
        return val
    return var
#
# Return the number of records in a pandas dataframe. 
# Returns 0 if the object is None.
#
def df_size(df):
    if(df is None):
        return 0
    if(df.shape[0] == 0):
        return 0
    return df.shape[0]

"""
Given a local directory path, get eligible files names from the path.
* If file_filter is specified in the config JSON, fetch file names with only the specified extension. E.g: .json 
"""
def get_files_in_path (path, file_filter):
    files_list = []
    for file in os.listdir(path):

        if file_filter != "":

            if file.endswith(file_filter):
                files_list.append(os.path.join(path, file))
        else:
            files_list.append(os.path.join(path, file))

    return files_list
    
    
class DateOps (object):
    def __init__(self, default_tz="US/Pacific"):
        self.default_tz = default_tz
    
    # Parse a string and convert into a datetime.
    def datetime_from_string(self, dtstr):
        return parse(dtstr)
    
    # Returns True is the date time is timezone aware. Else False
    def is_naive_datetime(self, dt):
        if (dt is None):
            return False

        if (dt.tzinfo is None):
            return False

        return True

    # Convert a naive datetime value to a timezone aware datetime
    # dt_naive: naive datetime
    # default_tz: timezone to which the naive time to be localized. E.g: "US/Pacific"
    # Returns a timezone aware datetime 
    #
    def localize_naive_datetime (self, dt_naive, default_tz="US/Pacific"):
        timezone = pytz.timezone(default_tz)
        d_aware = timezone.localize(dt_naive)
        return d_aware
    
    #
    # Convert a timezone aware datetime to UTC.
    #
    def convert_to_utc (self, dt_aware):
        target_tz = pytz.timezone('UTC')
        dt_utc = target_tz.normalize(dt_aware)
        return dt_utc
    
    #
    # Given a datetime string, convert it into datetime with UTC timezone
    #  -- parses datetime from the string
    #  -- localizes datetime to given/default timezone
    #  -- converts to UTC
    def from_string_to_utc (self, dtstr, default_tz="US/Pacific"):
        
        # If the input is a string....
        if (isinstance(dtstr, str)):
            # Parse the string into a date
            dt = self.datetime_from_string (dtstr)
        
        # If the input is a datetime....
        elif (isinstance(dtstr, datetime.datetime)):    
            dt = dtstr

        # check if the datetime is naive. If yes, localize
        if (not self.is_naive_datetime(dt)):
            dt = self.localize_naive_datetime (dt, default_tz)
            
        # now convert the datetime into UTC
        dt = self.convert_to_utc (dt)
        
        return dt
            
    #
    # Subtract two timezone aware datetime objects and return total seconds
    #
    def datetime_diff (self, dt1, dt2, unit="seconds" ):
        delta_seconds = (dt1 - dt2).total_seconds()
        
        retval = delta_seconds
        if (unit=="minutes"):
            retval = retval / 60.0
        
        if (unit == "hours"):
            retval = retval / (60.0 * 60.0)
        
        return  retval    
        