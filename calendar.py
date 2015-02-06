def recurs_desc(source):
    '''
    Recursive function to create the descriptions of all the courses given by
    source. The first assumption made is that the string 'NAME="C' preceeds all
    the courses (which it does in csc_short). So, 'start' is defined as the index
    where the function finds 'NAME="C' plus the length of the string until the
    course code starts (counted to be 28). The second assumption is that the
    string "DR=SCI" follows every description. 'end' is simply defined as the
    index where "DR=SCI" is found first after 'start'. 'start' and 'end' are
    used to create the final course description. Then, the string is passed
    into the function again, but with the index starting at where the first
    iteration ended (i.e., 'end').
    '''
    if source.find('NAME="C') == -1 : return []
    
    start = source.index('NAME="C') + 28
    end = source[start:].index("DR=SCI") + start
    cur_desc = source[start:end]
    
    return [cur_desc] + recurs_desc(source[end:])

def get_individual_courses(course_desc_page):
    '''
    Reads the file, then calls the recursive function recurs_desc to get the
    course description. Then returns the course description. The course
    description includes all html syntax, begins at where the course code
    starts and ends right before the string "DR=SCI" is found.
    '''
    page = open(course_desc_page, "r", encoding="utf-8").read()
    return recurs_desc(page)
    
def get_course_details(course_description):
    '''
    Retrieves the course code and the prerequisite description. Notice that if
    no prerequisite description is found, the function returns None. The
    prerequisite description is defined as:
    1. the string that proceeds the string "Prerequisite: " (found by indexing
    "Prereq" and counting the letters in "Prerequisite: ", i.e. 14), until
    2. there is a line break defined by "\n", with
    3. all " "'s stripped.
    Once the index of where the prerequisite description starts is found
    (denoted by 'prereq_loc'), the function simply returns the string with the
    definition above.
    '''
    if course_description.find("Prereq") == -1: return
    prereq_loc = course_description.index("Prereq") + 14
    return [course_description[:8], course_description[prereq_loc:course_description[prereq_loc:].index("\n")+prereq_loc].strip(" ")]

def prereq_str_to_list(prereq_str):
    '''
    Firstly, the function strips all html code from the prereq description.
    The <BR>'s are replaced with line breaks. The html code is assumed to begin
    whenever a '<' is enountered and end whenever a '>' is encountered.
    Then, the function appends whatever valid punctuation or courses it finds
    to a list called 'lis'. Courses are assumed to contain 'H1' or 'Y1', and
    begin with either C (for CSC) or S (for STA). There is one condition where
    the course code is given as '/nnnH1', where the n's are integers, instead
    of 'CSCnnnH1', so this function takes care of that too.
    '''
    punct = ["/", ",", ".", ";"]
    lis = []

    while prereq_str.find("<") != -1:
        if prereq_str[prereq_str.index("<"):prereq_str.index(">")+1] == "<BR>":prereq_str = prereq_str.replace("<BR>", "\n")
        else: prereq_str = prereq_str.replace(prereq_str[prereq_str.index("<"):prereq_str.index(">")+1], "")
    
    for i, j in enumerate(prereq_str):
        if j in punct: lis.append(j)
        elif j in ["H", "Y"] and prereq_str[i+1] == "1":
            if prereq_str[i-6] == "C" or prereq_str[i-6] == "S":
                lis.append(prereq_str[i-6:i+2])
            else:lis.append("CSC" + prereq_str[i-3:i+2])
    return lis

def is_course(string):
    '''
    Returns whether a string is a course or not, by trying to find 'H1' or
    'Y1' in the string (in accordance with assumption set above).
    '''
    return string.find("H1") != -1 or string.find("Y1") != -1

def expand_one_or(course_lists):
    '''
    Firstly, the function tried to find the "/" somewhere in the list of lists.
    If it is found, the index is stored in 'slash_loc', and if not, the function
    returns -1. slash_loc and its associated value are stored back into i and j
    so that we can pretend we are working still in the iterative loope (makes
    variable names shorter). 'loc' is used to store the index where the "/"
    appears in j. Then, the boundary condition where the "/" is at the
    beginning or the end of j is checked. Then, the condition where the adjacent
    values are courses is checked. If these two conditions do not hold true,
    then j is popped.
    
    Also, the expand_one_or list of lists and individual lists are sorted at the
    end.
    '''
    found_slash = False
    
    for i, j in enumerate(course_lists):
        if "/" in j:
            slash_loc = i
            found_slash = True
            break
    
    if found_slash == False: return -1    
    
    i, j = slash_loc, course_lists[slash_loc]
    
    loc = j.index("/")
    
    if loc-1 < 0 or loc+1 >= len(j):
        j.pop(loc)
        course_lists[i] = j
    elif is_course(j[loc-1]) and is_course(j[loc+1]):
        #Makes two identical but independent lists, and removes the values from
        #both lists as per the assignment. Then, both lists are added back into
        #course_lists, one after the other, while removing the original
        #course_lists[i].
        j1 = j[:]
        del j1[loc]
        del j1[loc-1]
        del j[loc+1]
        del j[loc]
        j = [j, j1]
        course_lists[i] = j[0]
        course_lists.insert(i+1, j[1])
    else:
        j.pop(loc)
        course_lists[i] = sorted(j)
        
    return sorted(course_lists)

def expand_all_ors(course_lists):
    '''
    Calls expand_one_or continuously until there are no more "/"'s (i.e., when
    the next iteration of expand_one_or(course_lists) is -1. The while loop
    breaks as soon as expand_one_or returns -1, i.e. when there are no "/"'s
    found. Then, duplicates are removed.
    '''
    while expand_one_or(course_lists) != -1:
        ecourse_lists = expand_one_or(course_lists)
    
    rem_dupes = []
    for i in course_lists:
        if i not in rem_dupes:
            rem_dupes.append(i)
            
    return rem_dupes
    
def build_prerequisite_dict(course_desc_page):
    '''
    Returns the dictionary of courses with their respective prerequisites. The
    function passes the source code into the functions written as answers for
    part a) to e) of Q1 to retrieve a list of prereqs with all ors expanded
    stored in 'prereq'. The 'temp' variable is used to store the course details
    for the current course so we can check if get_course_details returned None.
    The enumerate(prereq) loop gets rid of all list elements in prereqs that are
    not courses as per the is_course() function. The prereq list is added to the
    dictionary with its respective course code as long as there were detected,
    acceptable prerequisites (i.e. prereq != [[]]).
    
    Note that this function uses the answers from a) to e), and therefore makes
    the same assumptions that were made in the docstrings for a) to e) (i.e.,
    it was only tested to work with the csc_short.htm file).
    '''
    final_dict = {}
    for i in get_individual_courses(course_desc_page):
        temp = get_course_details(i)
        if temp != None:
            prereq = expand_all_ors([prereq_str_to_list(temp[1])])
            for j, k in enumerate(prereq):
                courses_only = []
                for l in k:
                    if is_course(str(l)) and l not in courses_only: courses_only.append(l)
                prereq[j] = sorted(courses_only)
                    
            if prereq != [[]]: final_dict[temp[0]] = sorted(prereq)
            
    return final_dict

def expand_inter(req, rdict, checked):
    '''
    This function takes in a list of prereqs 'req', a prereq dict
    'rdict', and a list of previously checked courses 'checked'. The previously
    checked courses are denoted by a concatenation of the course code and the
    index where it appeared (to avoid error in cases similar to Test 6). The 
    local variables do the following: 'replace' is a dictionary that has keys
    representing which index in 'req' to replace, and values representing what
    to replace it with, 'checked2' is a local variable that keeps track of what
    needs to be added to 'checked' after the function returns, and 'req2' is
    just a copy of req to work with locally.
    
    The function runs through 'req2' and if there is a course that has prereqs
    (is in rdict) and hasnt been checked yet, then the function will include it
    in 'replace' to be replaced. 
    
    HOWEVER, THE TEAM KNOWS THAT THERE IS AN ERROR WITH THIS FUNCTION. We 
    suspect some code similar to the ones commented out will help, but if the
    code is un-commented, the program goes on an infinite loop.
    
    The replacements are made, and duplicates are removed (partly using
    list(set()) trick). Then a final list of prereqs 'fin_req' is returned.
    '''
    replace = {}
    checked2 = []
    req2 = req[:]
    for x, i in enumerate(req2):
        temp = i[:]
        for j in temp:
            if j in rdict and j not in checked:
                no_extends = len(rdict[j])
                for y, k in enumerate(rdict[j]):
                    if x not in replace:
                        replace[x] = [i+k]                
                    if x in replace and no_extends == 1:
                        replace[x][y-1].extend(k)
                    
                    #else:
                        #replace[x].append(i+k)
                        
                checked2.append(j+str(x))
    
    for i in sorted(replace)[::-1]:
        req2[i] = replace[i][0]
        if len(replace[i]) > 1:
            for x, j in enumerate(replace[i][1:]):
                req2.insert(i+x, j)
                
    for i, j in enumerate(req2):
        req2[i] = sorted(list(set(j)))
    fin_reqs = []
    for i in req2:
        if i not in fin_reqs:
            fin_reqs.append(i)
                
    return [checked2, fin_reqs]
    
def get_all_paths_to_course(course_code, init_prereq_dict):
    '''
    Takes care of case where 'course_code' has no prereqs. Then, runs the 
    expand_iter function once to instantiate some variables. After that, it 
    loops until 'checked' doesn't change, i.e. when there are no more prereqs
    to check.
    '''
    if course_code not in init_prereq_dict:
        return [[]]
    
    checked = []
    result = expand_inter(init_prereq_dict[course_code], init_prereq_dict, checked)
    final_lis = result[1]
    checked.extend(result[0])
    checked = list(set(checked))
    
    same_check = False
    while not same_check:
        result = expand_inter(final_lis, init_prereq_dict, checked)
        final_lis = result[1]
        checked.extend(result[0])
        checked = list(set(checked))
        same_check = result[0] == expand_inter(final_lis, init_prereq_dict, checked)[0]
    
    return final_lis

if __name__ == '__main__':
    
    print('\nTest Case 0')#---------------------------------------------------------
    #Test for Question 1. Since build_prerequisite_dict() uses all parts of Q1,
    # the fact that this works means that all of Q1's functions work, at least
    # for csc.short.htm
    reqs_init = build_prerequisite_dict("csc_short.htm")
    print (reqs_init)
    
    print('\nTest Case 1')#---------------------------------------------------------
    #Lower Bound Case: Course key is not in dict, therefore no prereqs
    
    dict_1 = {"C": [["B"]]}
    expected = [[]]                         #Should be no way of taking course
    result = get_all_paths_to_course('A', dict_1)
    print(expected == result)
    
    print('\nTest Case 2')#-----------------------------------------------------
    #Starter Case: list has only one element and no prerequisites
    
    dict_2 = {"A": [["B"]]}
    expected = [["B"]]                      #Only one prereq is required
    result = get_all_paths_to_course('A', dict_2)
    print(expected == result)
    
    print('\nTest Case 3')#-----------------------------------------------------
    #No Expansion: final list is identical to the list expansion (but only
    # one element per sublist)
    
    dict_3 = {"A": [["B"], ["C"]]}
    expected = [["B"], ["C"]]               #Both are equal prereqs for course
    result = get_all_paths_to_course('A', dict_3)
    print(expected == result) 
    
    print('\nTest Case 4')#-----------------------------------------------------
    #Basic Expansion: function must expand the simplest list once for the final

    dict_4 = {"A": [["B"]],
              "B": [["C"]]}
    expected = [["B", "C"]]                 #Only one path of Pre-reqs in order
    result = get_all_paths_to_course('A', dict_4)
    print(expected == result)
    
    print('\nTest Case 5')#-----------------------------------------------------
    #Double Expansion: function must expand the simplest list twice

    dict_5 = {"A": [["B"]],
              "B": [["C"]],
              "C": [["D"]]}
    expected = [["B", "C", "D"]]            #Only one path of prereqs in order
    result = get_all_paths_to_course('A', dict_5)
    print(expected == result)
    
    print('\nTest Case 6')#-----------------------------------------------------
    #Double Expansion, multiple sublists in value list: function must expand
    # twice for the final answer but there are multiple sublists
    
    dict_6 = {"A": [["B"], ["C"]],
              "B": [["C"]],
              "C": [["D"]]}
    expected = [["B", "C", "D"], ["C", "D"]]    #Expands in order properly
    result = get_all_paths_to_course('A', dict_6)
    print(expected == result)
    
    print('\nTest Case 7')#-----------------------------------------------------
    #No Expansion, multiple elements in sublist: function must expand
    # the sub-list (assuming no pre-reqs for each)
        
    dict_7 = {"A": [["B", "C"]]}
    expected = [["B", "C"]]                 #Path requires both courses
    result = get_all_paths_to_course('A', dict_7)
    print(expected == result)
    
    print('\nTest Case 8')#-----------------------------------------------------
    #Single Expansion, multiple elements in sublist: function must expand
    # the sub-list (assuming one prereq for each)
            
    dict_8 = {"A": [["B", "C"]],
              "B": [["D"]],
              "C": [["E"]]}
    expected = [["B", "C", "D", "E"]]       #Path requires expansion of B and C
    result = get_all_paths_to_course('A', dict_8)
    print(expected == result)
    
    print('\nTest Case 9')
    #Multiple elements in one sublist, not in other: function must expand both
    # the sub-lists (assuming one prereq for each)
                
    dict_9 = {"A": [["B", "C"], ["C"]],
              "B": [["D"]],
              "C": [["E"]]}
    expected = [["B", "C", "D", "E"],
                ["C", "E"]]                #Path expands like Test 8 
    result = get_all_paths_to_course('A', dict_9)
    print(expected == result)
    
    print('\nTest Case 10')#----------------------------------------------------
    #Multiple elements in sublist and (optional) elements in value sublists:
    # function must expand the sublists, keeping in mind that the value sublists
    # have multiple possible prereqs
                    
    dict_10 = {"A": [["B", "C"], ["C"]],
              "B": [["D"], ["F"]],
              "C": [["E"]]}
    expected = [["B", "C", "D", "E"], 
                ["B", "C", "E", "F"],
                ["C", "E"]] 
    result = get_all_paths_to_course('A', dict_10)
    print(expected == result)    
    
    print('\nTest Case 11')#----------------------------------------------------
    #Upper Bound Case: Multiple sublists, elements, values sublists/elements:
    # This is a combination of everything, with multiple sublists and elements
    # for the main sublist and the value sublists
                        
    dict_11 = {"A": [["B", "C"], ["C"]],
               "B": [["D", "F"], ["G"]],
               "C": [["E"]]}
    expected = [["B", "C", "D", "E", "F"], 
                ["B", "C", "E", "G"],
                ["C", "E"]] 
    result = get_all_paths_to_course('A', dict_11)
    print(expected == result)
    
    print('\nTest Case 12')#----------------------------------------------------
    #Guerzhoy Given Test 1: Test the example with the ABCD list
    
    dict_12 = {"A": [ ["B"], ["C"] ], 
               "B": [ ["D"], ["E"] ], 
               "D": [ ["F"], ["G"] ],
               "C": [ ["H"] ] }    
    expected = [ ["B", "D", "F"],
                 ["B", "D", "G"],
                 ["B", "E"],
                 ["C", "H"] ]
    result = get_all_paths_to_course('A', dict_12)
    print(expected == result)
    
    print('\nTest Case 13')#----------------------------------------------------
    #Guerzhoy Given Test 2: Test the example with Part 1's answer (assumed to be
    # correct) and the paths
    
    expected = [ ["CSC108H1", "CSC148H1"], 
                 ["CSC108H1", "CSC148H1", "CSC150H1"],
                 ["CSC108H1", "CSC148H1", "CSC165H1"],
                 ["CSC108H1", "CSC148H1", "CSC240H1"],
                 ["CSC150H1", "CSC165H1"],
                 ["CSC150H1", "CSC240H1"] ]
    result = get_all_paths_to_course('CSC258H1', reqs_init)
    print(expected == result)    
