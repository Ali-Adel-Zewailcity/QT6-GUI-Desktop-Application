from typing import Tuple, Any

# Global Variables used to control style pallete of text output on CLI
red = '\033[31m'
yellow = '\033[33m'
shade = '\033[2m'
end = '\033[0m'


def while_input(input: str, options: list) -> bool:
    '''
    Checks if user input is a valid option and if not valid it returns True
    
    *used inside while loops where if input is not valid the loop will never end untill the users
    enter a valid option*
    '''
    if input in options: 
        return False
    else:
        print(f'{red}Error!{end} {shade}Please enter a valid number.{end}')
        return True

def proceed():
    'Returns True if user chooses to proceed otherwise returns False'
    return input(f'{yellow}Proceed process (Y\\n): {end}').lower() == 'y'

def pdf_split_handle_input(doc, start: str, end: str) -> Tuple[int, int]:
    '''Check if start page is before than end page and also check both is before the last page in the PDF'''
    assert start.isdigit() and end.isdigit(), "User did not enter valid page number"
    start, end = int(start), int(end)
    pages = len(doc)
    end = pages if end > pages else end
    start = pages if start > pages else start
    start, end = (end, start) if (start > end) else (start, end)
    return start, end

def pdf_pd_input(nums: Any) -> tuple:
    '''
    Used to handle this different patterns of input single page:1 | range of pages:1-8 | pages:1,7,4,6
    
    return tuple containg all pages index to be deleted
    '''
    return [int(nums)-1] if len(nums) == 1 else tuple(set(int(i)-1 for i in nums.split(',')))\
        if nums.find(',') != -1\
        else tuple(range(int(nums.split('-')[0])-1, int(nums.split('-')[1])))

def calculate_sec(start: str, end: str) -> str:
    '''Checks Input Time is in format `HH:MM:SS`, `MM:SS`, `SS` and unify into single format: `SS`
    
    **Return** Time passed in seconds `SS` 
    '''
    s = start.split(":")
    e = end.split(":")
    
    if len(s) != len(e):
        raise Exception("Start Time and End Time must be in the same foramt")
    
    for i in (s, e):
        for j in i:
            assert j.isdigit(), f"Time is not Specified Correctly: {":".join(i)}"

    difference = 0

    for i in range(-len(s), 0):
        if i == -3:
            difference += (float(e[i]) - float(s[i])) * 60 * 60
        elif i == -2:
            difference += (float(e[i]) - float(s[i])) * 60
        elif i == -1:
            difference += float(e[i]) - float(s[i])
    return str(difference)