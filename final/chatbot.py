from pyswip import Prolog
import re
from pyswip.prolog import PrologError

prolog = Prolog()
prolog.consult("family.pl")

def is_valid_name(name):
    """Check if a name is valid (only letters, not a reserved word)"""
    # Reserved words that should not be accepted as names
    reserved_words = ['who', 'what', 'where', 'when', 'why', 'how', 'is', 'are', 
                      'the', 'a', 'an', 'and', 'or', 'not', 'if', 'then']
    
    # Check if name contains only letters
    if not name.isalpha():
        return False
    
    # Check if name is a reserved word (case-insensitive)
    if name.lower() in reserved_words:
        return False
    
    return True

def assert_once(fact):
    """Assert a fact only if it doesn't already exist"""
    try:
        if not list(prolog.query(fact)):
            prolog.assertz(fact)
            return "new"  # New fact added
        else:
            return "exists"  # Fact already exists
    except PrologError as e: 
        print(f"DEBUG: PrologError: {e}")
        return "error"  # Error occurred

def check_self_relation(a, b):
    """Check if someone is trying to relate to themselves"""
    return a.lower() == b.lower()

def check_contradiction(person, gender, relation=None, other_person=None):
    """Check if adding this fact would create a contradiction"""
    person = person.lower()
    
    try:
        # Check gender contradiction
        opposite_gender = "female" if gender == "male" else "male"
        if list(prolog.query(f"{opposite_gender}({person})")):
            return True
        
        # Also check if this would create a gender conflict
        if list(prolog.query(f"gender_conflict({person})")):
            return True
        
        # Check for impossible self-relations
        if other_person and check_self_relation(person, other_person):
            return True
        
        # Check for circular parent relationships (A parent of B, B parent of A)
        if relation == "parent" and other_person:
            other_person = other_person.lower()
            if list(prolog.query(f"parent({other_person}, {person})")):
                return True
    except PrologError:
        return False
    
    return False

def check_would_create_cycle(new_parent, new_child):
    """Check if adding parent(new_parent, new_child) would create a cycle"""
    new_parent, new_child = new_parent.lower(), new_child.lower()
    
    # Self-relation check
    if new_parent == new_child:
        return True
    
    try:
        # Check if new_child is already an ancestor of new_parent
        result = list(prolog.query(f"ancestor({new_child}, {new_parent})"))
        return bool(result)
    except PrologError:
        return False

def safe_prolog_query(query):
    """Safely execute a Prolog query with error handling"""
    try:
        return list(prolog.query(query))
    except PrologError as e:
        print(f"Debug: Prolog error for query '{query}': {e}")
        return []

def levenshtein_distance(s1, s2):
    """Calculate the Levenshtein distance between two strings"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def correct_relationship_typo(word):
    """Comprehensive typo correction for relationship words"""
    word = word.lower()
    
    # Valid relationship types
    valid_relations = ['father', 'mother', 'son', 'daughter', 'brother', 'sister', 
                      'grandfather', 'grandmother', 'uncle', 'aunt', 'child', 'parent',
                      'husband', 'wife', 'spouse', 'nephew', 'niece', 'cousin', 'sibling']
    
    # Manual corrections for common typos
    manual_corrections = {
        'gradfather': 'grandfather',
        'gradmother': 'grandmother',
        'granfather': 'grandfather',
        'granmother': 'grandmother',
        'garndfather': 'grandfather',
        'garndmother': 'grandmother',
        'grandfater': 'grandfather',
        'grandmothr': 'grandmother',
        'grandfther': 'grandfather',
        'husban': 'husband',       
        'huband': 'husband',     
        'wif': 'wife',            
        'wyfe': 'wife',          
        'husbadn': 'husband',
        'nefew': 'nephew',        
        'nphew': 'nephew',       
        'newphew': 'nephew',      
        'neice': 'niece',        
        'nece': 'niece',          
        'neese': 'niece',        
        'cousen': 'cousin',     
        'cusin': 'cousin',        
        'couson': 'cousin',       
        'fater': 'father',
        'fahter': 'father',
        'fathr': 'father',
        'mther': 'mother',
        'mothr': 'mother',
        'mothre': 'mother',
        'broter': 'brother',
        'brothr': 'brother',
        'brothe': 'brother',
        'siter': 'sister',
        'sistre': 'sister',
        'siseter': 'sister',
        'childre': 'children',
        'childen': 'children',
        'chilren': 'children',
        'chlidren': 'children',
        'daugther': 'daughter',
        'daughtr': 'daughter',
        'uncl': 'uncle',
        'anut': 'aunt',
        'siblig': 'sibling',
        'spous': 'spouse',     
        'spouce': 'spouse',     
        'spoose': 'spouse', 
    }
    
    if word in manual_corrections:
        return manual_corrections[word]
    
    # Handle plural forms
    if word.endswith('s') and word[:-1] in valid_relations:
        return word[:-1]
    
    # Handle special case for children -> child
    if word == 'children':
        return 'child'
    
    # Check exact match
    if word in valid_relations:
        return word
    
    # Fuzzy matching with Levenshtein distance
    best_match = None
    best_distance = float('inf')
    threshold = 2  # Maximum allowed edit distance
    
    for valid_word in valid_relations:
        distance = levenshtein_distance(word, valid_word)
        if distance <= threshold and distance < best_distance:
            best_distance = distance
            best_match = valid_word
    
    return best_match

def get_parents(person):
    """Get all parents of a person"""
    result = safe_prolog_query(f"parent(P, {person})")
    return {r["P"] for r in result if "P" in r}

def handle_sibling_with_smart_inference(person1, person2, rel):
    """Handle sibling relationships with automatic parent inference"""
    
    # Get existing parents for both people
    parents1 = get_parents(person1)
    parents2 = get_parents(person2)
    
    # Case 1: They already share at least one parent
    shared_parents = parents1.intersection(parents2)
    if shared_parents:
        return "OK! I already knew they were siblings through their shared parent(s)."
    
    # Case 2: One has parents, the other doesn't
    if parents1 and not parents2:
        for parent in parents1:
            assert_once(f"parent({parent}, {person2})")
        return "OK! I learned something."
    
    elif parents2 and not parents1:
        for parent in parents2:
            assert_once(f"parent({parent}, {person1})")
        return "OK! I learned something."
    
    # Case 3: Neither has parents - we need to create a shared parent
    elif not parents1 and not parents2:
        return "OK! I learned something."
    
    # Case 4: Both have different parents - make them share all parents
    else:
        all_parents = parents1.union(parents2)
        for parent in all_parents:
            assert_once(f"parent({parent}, {person1})")
            assert_once(f"parent({parent}, {person2})")
        
        parent_names = ', '.join(p.capitalize() for p in all_parents)
        return f"OK! I learned that both {person1.capitalize()} and {person2.capitalize()} have {parent_names} as their parents, making them full siblings."

# === Statement Parsing ===

def parse_statement(prompt):
    prompt = prompt.strip().rstrip(".")
    
    # Handle empty input
    if not prompt:
        return "Please tell me something!"

    patterns = [
        (r"(\w+) is (?:a |an |the )?(father|mother|parent|child|son|daughter|brother|sister|sibling|uncle|aunt|grandfather|grandmother|husband|wife|spouse|nephew|niece|cousin) of (\w+)", handle_single_relation),
        (r"(\w+) and (\w+) are siblings", handle_siblings),
        (r"(\w+) and (\w+) are (brothers?|sisters?) of (\w+)", handle_siblings_of),
        (r"(\w+) and (\w+) are cousins", handle_cousins),
        (r"(\w+) and (\w+) are spouses", handle_spouses),            
        (r"(\w+) and (\w+) are (?:the )?parents of (\w+)", handle_parents),
        (r"(\w+) and (\w+) are children of (\w+)", handle_two_children),
        (r"(\w+), (\w+)(?:, and (\w+))? are children of (\w+)", handle_children),
        (r"(\w+) is (?:a |an |the )?child of (\w+)", handle_child_relation),
        (r"(\w+) and (\w+) are married", handle_marriage),        
        (r"(\w+) is married to (\w+)", handle_marriage_to),        
        (r"(\w+) has (?:a |an |the )?(son|daughter|child|husband|wife|spouse|nephew|niece|cousin) (?:named )?(\w+)", handle_has_child),
        (r"(\w+) and (\w+) have (?:a |an |the )?child (?:named )?(\w+)", handle_have_child)
    ]

    for i, (pattern, handler) in enumerate(patterns):
        match = re.match(pattern, prompt, re.IGNORECASE)
        if match:
            try:
                return handler(match)
            except Exception as e:
                return f"Sorry, I encountered an error processing that statement: {str(e)}"

    return "Sorry, I can't understand that statement format. Try using patterns like 'X is the father of Y' or 'X and Y are siblings'."

def handle_single_relation(match):
    a, rel, b = match.groups()
    a, b = a.lower(), b.lower()

    # Validate names using the new function
    if not is_valid_name(a) or not is_valid_name(b):
        if a.lower() == 'who' or b.lower() == 'who':
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"

    if check_self_relation(a, b):
        return "That's impossible!"

    # Determine gender based on relation
    if rel in ["father", "son", "brother", "uncle", "nephew", "grandfather", "husband"]:
        gender = "male"
    elif rel in ["mother", "daughter", "sister", "aunt", "niece", "grandmother", "wife"]:
        gender = "female"
    else:
        gender = None
    
    # Check for contradictions
    if gender and check_contradiction(a, gender):
        return "That's impossible!"
    
    # Handle different relationship types
    if rel in ["father", "mother", "parent"]:
        if check_would_create_cycle(a, b):
            return "That's impossible!"
        result = assert_once(f"parent({a}, {b})")
        if result == "error":
            return "Error adding that relationship!"
        elif result == "exists":
            return "OK! I already knew that."
        
    elif rel in ["son", "daughter", "child"]:
        if check_would_create_cycle(b, a):
            return "That's impossible!"
        result = assert_once(f"parent({b}, {a})")
        if result == "error":
            return "Error adding that relationship!"
        elif result == "exists":
            return "OK! I already knew that."

    elif rel in ["brother", "sister", "sibling"]:
        # Handle sibling relationship with smart inference
        result = handle_sibling_with_smart_inference(a, b, rel)
        if gender:
            assert_once(f"{gender}({a})")
        return result
        
    elif rel in ["grandfather", "grandmother"]:
        if check_would_create_cycle(a, b):
            return "That's impossible!"
        result = assert_once(f"grandparent({a}, {b})")
        if result == "error":
            return "Error adding that relationship!"
        elif result == "exists":
            return "OK! I already knew that."
        
    elif rel in ["uncle", "aunt"]:
        result = assert_once(f"{rel}({a}, {b})")
        if result == "error":
            return "Error adding that relationship!"
        elif result == "exists":
            return "OK! I already knew that."
        
    elif rel in ["nephew", "niece"]:
        result = assert_once(f"{rel}({a}, {b})")
        if result == "error":
            return "Error adding that relationship!"
        elif result == "exists":
            return "OK! I already knew that."
        
    elif rel == "cousin":
        existing = safe_prolog_query(f"cousin({a}, {b})")
        if existing:
            return "OK! I already knew that."
        # Add symmetric cousin relationship
        assert_once(f"cousin({a}, {b})")
        assert_once(f"cousin({b}, {a})")
        
    elif rel in ["husband", "wife", "spouse"]:
        existing_spouse_a = safe_prolog_query(f"married({a}, _)")
        existing_spouse_b = safe_prolog_query(f"married({b}, _)")
        
        if existing_spouse_a:
            return f"That's impossible! {a.capitalize()} is already married."
        if existing_spouse_b:
            return f"That's impossible! {b.capitalize()} is already married."
        
        existing_marriage = safe_prolog_query(f"married({a}, {b})") or safe_prolog_query(f"married({b}, {a})")
        if existing_marriage:
            return "OK! I already knew that."
            
        result1 = assert_once(f"married({a}, {b})")
        result2 = assert_once(f"married({b}, {a})")
        if result1 == "error" or result2 == "error":
            return "Error adding that relationship!"

    # Assert gender after all checks pass (for new facts)
    if gender:
        assert_once(f"{gender}({a})")

    return "OK! I learned something."

def handle_siblings(match):
    a, b = match.groups()
    a, b = a.lower(), b.lower()

    if not is_valid_name(a) or not is_valid_name(b):
        if a.lower() == 'who' or b.lower() == 'who':
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"

    if check_self_relation(a, b):
        return "That's impossible!"

    # Use the same smart inference logic as handle_single_relation
    return handle_sibling_with_smart_inference(a, b, "sibling")

def handle_siblings_of(match):
    """Handle 'X and Y are brothers/sisters of Z'"""
    person1, person2, relation, target = match.groups()
    person1, person2, target = person1.lower(), person2.lower(), target.lower()
    
    # Validate names
    if not all(is_valid_name(name) for name in [person1, person2, target]):
        if 'who' in [person1.lower(), person2.lower(), target.lower()]:
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"
    
    # Check for self-relations
    if target in [person1, person2]:
        return "That's impossible!"
    
    # Determine gender from relation
    if relation.startswith('brother'):
        gender1 = gender2 = "male"
    else:  # sisters
        gender1 = gender2 = "female"
    
    # Check for gender contradictions
    if check_contradiction(person1, gender1) or check_contradiction(person2, gender2):
        return "That's impossible!"
    
    # Use the smart sibling inference for both relationships
    result1 = handle_sibling_with_smart_inference(person1, target, relation)
    result2 = handle_sibling_with_smart_inference(person2, target, relation)
    
    # Assert genders
    assert_once(f"{gender1}({person1})")
    assert_once(f"{gender2}({person2})")
    
    # Also make person1 and person2 siblings of each other
    handle_sibling_with_smart_inference(person1, person2, relation)
    
    return "OK! I learned something."

def handle_cousins(match):
    """Handle 'X and Y are cousins'"""
    a, b = match.groups()
    a, b = a.lower(), b.lower()

    if not is_valid_name(a) or not is_valid_name(b):
        if a.lower() == 'who' or b.lower() == 'who':
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"

    if check_self_relation(a, b):
        return "That's impossible!"

    # Check if cousin relationship already exists
    existing = safe_prolog_query(f"cousin({a}, {b})")
    if existing:
        return "OK! I already knew that."

    # Assert cousin relationship (symmetric)
    assert_once(f"cousin({a}, {b})")
    assert_once(f"cousin({b}, {a})")
    
    return "OK! I learned something."

def handle_spouses(match):
    """Handle 'X and Y are spouses'"""
    a, b = match.groups()
    a, b = a.lower(), b.lower()

    if not is_valid_name(a) or not is_valid_name(b):
        if a.lower() == 'who' or b.lower() == 'who':
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"

    if check_self_relation(a, b):
        return "That's impossible!"

    # Check for existing marriages (prevent bigamy)
    existing_spouse_a = safe_prolog_query(f"married({a}, _)")
    existing_spouse_b = safe_prolog_query(f"married({b}, _)")
    
    if existing_spouse_a:
        return f"That's impossible! {a.capitalize()} is already married."
    if existing_spouse_b:
        return f"That's impossible! {b.capitalize()} is already married."

    # Check if this exact marriage already exists in either direction
    existing_marriage = safe_prolog_query(f"married({a}, {b})") or safe_prolog_query(f"married({b}, {a})")
    if existing_marriage:
        return "OK! I already knew that."

    # Assert both directions
    result1 = assert_once(f"married({a}, {b})")
    result2 = assert_once(f"married({b}, {a})")
    if result1 == "error" or result2 == "error":
        return "Error adding that relationship!"
    
    return "OK! I learned something."

def handle_parents(match):
    a, b, c = match.groups()
    a, b, c = a.lower(), b.lower(), c.lower()

    if not all(is_valid_name(name) for name in [a, b, c]):
        if 'who' in [a.lower(), b.lower(), c.lower()]:
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"

    if c in [a, b]:
        return "That's impossible!"
    
    if check_would_create_cycle(a, c) or check_would_create_cycle(b, c):
        return "That's impossible!"

    # Check if relationships already exist
    existing1 = safe_prolog_query(f"parent({a}, {c})")
    existing2 = safe_prolog_query(f"parent({b}, {c})")
    
    if existing1 and existing2:
        return "OK! I already knew that."

    result1 = assert_once(f"parent({a}, {c})")
    result2 = assert_once(f"parent({b}, {c})")
    
    if result1 == "error" or result2 == "error":
        return "Error adding that relationship!"
    
    # If one was new and one existed, still say we learned something
    if result1 == "new" or result2 == "new":
        return "OK! I learned something."
    else:
        return "OK! I already knew that."

def handle_children(match):
    groups = match.groups()
    parent = groups[-1].lower()
    children = [name.lower() for name in groups[:-1] if name and name.isalpha()]

    if not is_valid_name(parent):
        if parent.lower() == 'who':
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"

    all_exist = True
    for child in children:
        if not is_valid_name(child):
            if child.lower() == 'who':
                return "Invalid name! 'Who' is a reserved word for questions."
            return "Names should only contain letters and cannot be reserved words!"
        if check_self_relation(child, parent):
            return "That's impossible!"
        if check_would_create_cycle(parent, child):
            return "That's impossible!"
        result = assert_once(f"parent({parent}, {child})")
        if result == "new":
            all_exist = False
    
    return "OK! I already knew that." if all_exist else "OK! I learned something."

def handle_two_children(match):
    """Handle 'X and Y are children of Z'"""
    child1, child2, parent = match.groups()
    child1, child2, parent = child1.lower(), child2.lower(), parent.lower()
    
    if not all(is_valid_name(name) for name in [child1, child2, parent]):
        if 'who' in [child1.lower(), child2.lower(), parent.lower()]:
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"
    
    if child1 == parent or child2 == parent:
        return "That's impossible!"
    
    if check_would_create_cycle(parent, child1) or check_would_create_cycle(parent, child2):
        return "That's impossible!"
    
    # Check if relationships already exist
    existing1 = safe_prolog_query(f"parent({parent}, {child1})")
    existing2 = safe_prolog_query(f"parent({parent}, {child2})")
    
    if existing1 and existing2:
        return "OK! I already knew that."
    
    result1 = assert_once(f"parent({parent}, {child1})")
    result2 = assert_once(f"parent({parent}, {child2})")
    
    if result1 == "new" or result2 == "new":
        return "OK! I learned something."
    else:
        return "OK! I already knew that."
    
def handle_child_relation(match):
    child, parent = match.groups()
    child, parent = child.lower(), parent.lower()
    
    if not is_valid_name(child) or not is_valid_name(parent):
        if child.lower() == 'who' or parent.lower() == 'who':
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"
    
    if check_self_relation(child, parent):
        return "That's impossible!"
    
    if check_would_create_cycle(parent, child):
        return "That's impossible!"
    
    result = assert_once(f"parent({parent}, {child})")
    if result == "error":
        return "Error adding that relationship!"
    elif result == "exists":
        return "OK! I already knew that."
    return "OK! I learned something."

def handle_marriage(match):
    """Handle 'X and Y are married'"""
    a, b = match.groups()
    a, b = a.lower(), b.lower()

    if not is_valid_name(a) or not is_valid_name(b):
        if a.lower() == 'who' or b.lower() == 'who':
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"

    if check_self_relation(a, b):
        return "That's impossible!"

    # Check for existing marriages (prevent bigamy)
    existing_spouse_a = safe_prolog_query(f"married({a}, _)")
    existing_spouse_b = safe_prolog_query(f"married({b}, _)")
    
    if existing_spouse_a:
        return f"That's impossible! {a.capitalize()} is already married."
    if existing_spouse_b:
        return f"That's impossible! {b.capitalize()} is already married."

    # Check if this exact marriage already exists in either direction
    existing_marriage = safe_prolog_query(f"married({a}, {b})") or safe_prolog_query(f"married({b}, {a})")
    if existing_marriage:
        return "OK! I already knew that."

    # Assert both directions
    result1 = assert_once(f"married({a}, {b})")
    result2 = assert_once(f"married({b}, {a})")
    if result1 == "error" or result2 == "error":
        return "Error adding that relationship!"
    
    return "OK! I learned something."

def handle_marriage_to(match):
    """Handle 'X is married to Y'"""
    a, b = match.groups()
    a, b = a.lower(), b.lower()

    if not is_valid_name(a) or not is_valid_name(b):
        if a.lower() == 'who' or b.lower() == 'who':
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"

    if check_self_relation(a, b):
        return "That's impossible!"

    # Check for existing marriages (prevent bigamy)
    existing_spouse_a = safe_prolog_query(f"married({a}, _)")
    existing_spouse_b = safe_prolog_query(f"married({b}, _)")
    
    if existing_spouse_a:
        return f"That's impossible! {a.capitalize()} is already married."
    if existing_spouse_b:
        return f"That's impossible! {b.capitalize()} is already married."

    # Check if this exact marriage already exists in either direction
    existing_marriage = safe_prolog_query(f"married({a}, {b})") or safe_prolog_query(f"married({b}, {a})")
    if existing_marriage:
        return "OK! I already knew that."

    # Assert both directions
    result1 = assert_once(f"married({a}, {b})")
    result2 = assert_once(f"married({b}, {a})")
    if result1 == "error" or result2 == "error":
        return "Error adding that relationship!"
    
    return "OK! I learned something."

def handle_has_child(match):
    parent, child_type, child = match.groups()
    parent, child = parent.lower(), child.lower()
    
    if not is_valid_name(parent) or not is_valid_name(child):
        if parent.lower() == 'who' or child.lower() == 'who':
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"
    
    if check_self_relation(parent, child):
        return "That's impossible!"
    
    if check_would_create_cycle(parent, child):
        return "That's impossible!"
    
    # Check if relationship already exists
    existing = safe_prolog_query(f"parent({parent}, {child})")
    if existing:
        return "OK! I already knew that."
    
    # Determine child's gender
    if child_type in ["son"]:
        assert_once(f"male({child})")
    elif child_type in ["daughter"]:
        assert_once(f"female({child})")
    
    result = assert_once(f"parent({parent}, {child})")
    if result == "error":
        return "Error adding that relationship!"
    
    return "OK! I learned something."

def handle_have_child(match):
    parent1, parent2, child = match.groups()
    parent1, parent2, child = parent1.lower(), parent2.lower(), child.lower()
    
    if not all(is_valid_name(name) for name in [parent1, parent2, child]):
        if 'who' in [parent1.lower(), parent2.lower(), child.lower()]:
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"
    
    if child in [parent1, parent2]:
        return "That's impossible!"
    
    if check_would_create_cycle(parent1, child) or check_would_create_cycle(parent2, child):
        return "That's impossible!"
    
    # Check if relationships already exist
    existing1 = safe_prolog_query(f"parent({parent1}, {child})")
    existing2 = safe_prolog_query(f"parent({parent2}, {child})")
    
    if existing1 and existing2:
        return "OK! I already knew that."
    
    result1 = assert_once(f"parent({parent1}, {child})")
    result2 = assert_once(f"parent({parent2}, {child})")
    
    if result1 == "new" or result2 == "new":
        return "OK! I learned something."
    else:
        return "OK! I already knew that."

# === Question Parsing ===

def parse_question(prompt):
    prompt = prompt.strip().rstrip("?")
    
    if not prompt:
        return "What would you like to know?"

    patterns = [
        (r"Is (\w+) (?:a |an |the )?(father|mother|parent|child|son|daughter|brother|sister|sibling|uncle|aunt|grandfather|grandmother|husband|wife|spouse|nephew|niece|cousin) of (\w+)", handle_yesno_relation),
        (r"Are (\w+) and (\w+) siblings", handle_yesno_sibling),
        (r"Are (\w+) and (\w+) cousins", handle_yesno_cousins),
        (r"Are (\w+) and (\w+) spouses", handle_yesno_spouses),       
        (r"Are (\w+) and (\w+) married", handle_yesno_married),
        (r"Is (\w+) married to (\w+)", handle_yesno_married_to),
        (r"Are (\w+) and (\w+) (?:the )?parents of (\w+)", handle_yesno_parents),
        (r"Are (\w+), (\w+)(?:, and (\w+))? children of (\w+)", handle_yesno_children),
        (r"Are (\w+) and (\w+) children of (\w+)", handle_yesno_two_children),
        (r"Who (?:is|are) (?:the |a |an )?(father|mother|parent|child|son|daughter|brother|sister|sibling|siblings|brothers|sisters|uncle|aunt|grandfather|grandmother|husband|wife|spouse|nephew|niece|cousin|children|parents|sons|daughters|uncles|aunts|nephews|nieces|cousins) of (\w+)", handle_list_query),
        (r"Who is (\w+) married to", handle_who_married_to),
        (r"Who is the spouse of (\w+)", handle_who_spouse),          
        (r"Are (\w+) and (\w+) relatives", handle_relative_question),
        (r"Does (\w+) have (?:a |an |any )?(son|daughter|child|husband|wife|spouse|nephew|niece|cousin|children) (?:named )?(\w+)", handle_has_relation_question),
        (r"How many (\w+) does (\w+) have", handle_count_question)
    ]

    for pattern, handler in patterns:
        match = re.match(pattern, prompt, re.IGNORECASE)
        if match:
            try:
                return handler(match)
            except Exception as e:
                return f"Sorry, I encountered an error: {str(e)}"

    return "I don't understand that question format. Try asking 'Is X the father of Y?' or 'Who are the children of X?'"

def handle_yesno_relation(match):
    a, rel, b = match.groups()
    a, b = a.lower(), b.lower()
    rel = rel.lower()
    
    # Validate names
    if not is_valid_name(a) or not is_valid_name(b):
        if a.lower() == 'who' or b.lower() == 'who':
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"
    
    # Use the enhanced typo correction
    corrected_rel = correct_relationship_typo(rel)
    
    if corrected_rel is None:
        # Find similar words for suggestions
        valid_relations = ['father', 'mother', 'son', 'daughter', 'brother', 'sister', 
                          'grandfather', 'grandmother', 'uncle', 'aunt', 'child', 'parent']
        suggestions = []
        for valid_rel in valid_relations:
            if valid_rel.startswith(rel[:2]) or rel[:2] in valid_rel or levenshtein_distance(rel, valid_rel) <= 3:
                suggestions.append(valid_rel)
        
        if suggestions:
            return f"I don't recognize '{rel}'. Did you mean: {', '.join(suggestions[:3])}?"
        else:
            return f"I don't recognize '{rel}'. Try: father, mother, son, daughter, brother, sister, grandfather, grandmother, uncle, aunt."
    
    rel = corrected_rel
    result = safe_prolog_query(f"{rel}({a}, {b})")
    return "Yes!" if result else "No."

def handle_yesno_sibling(match):
    a, b = match.groups()
    a, b = a.lower(), b.lower()
    
    if not is_valid_name(a) or not is_valid_name(b):
        if a.lower() == 'who' or b.lower() == 'who':
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"
    
    result = safe_prolog_query(f"sibling({a}, {b})")
    return "Yes!" if result else "No."

def handle_yesno_cousins(match):
    """Handle 'Are X and Y cousins?'"""
    a, b = match.groups()
    a, b = a.lower(), b.lower()
    
    if not is_valid_name(a) or not is_valid_name(b):
        if a.lower() == 'who' or b.lower() == 'who':
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"
    
    result = safe_prolog_query(f"cousin({a}, {b})")
    return "Yes!" if result else "No."

def handle_yesno_spouses(match):
    """Handle 'Are X and Y spouses?'"""
    a, b = match.groups()
    a, b = a.lower(), b.lower()
    
    if not is_valid_name(a) or not is_valid_name(b):
        if a.lower() == 'who' or b.lower() == 'who':
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"
    
    if check_self_relation(a, b):
        return "No."
    
    result = safe_prolog_query(f"spouse({a}, {b})")
    return "Yes!" if result else "No."

def handle_yesno_married(match):
    """Handle 'Are X and Y married?'"""
    a, b = match.groups()
    a, b = a.lower(), b.lower()
    
    if not is_valid_name(a) or not is_valid_name(b):
        if a.lower() == 'who' or b.lower() == 'who':
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"
    
    if check_self_relation(a, b):
        return "No."
    
    result = safe_prolog_query(f"married({a}, {b})")
    return "Yes!" if result else "No."

def handle_yesno_married_to(match):
    """Handle 'Is X married to Y?'"""
    a, b = match.groups()
    a, b = a.lower(), b.lower()
    
    if not is_valid_name(a) or not is_valid_name(b):
        if a.lower() == 'who' or b.lower() == 'who':
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"
    
    if check_self_relation(a, b):
        return "No."
    
    result = safe_prolog_query(f"married({a}, {b})")
    return "Yes!" if result else "No."

def handle_yesno_children(match):
    groups = match.groups()
    parent = groups[-1].lower()
    children = [name.lower() for name in groups[:-1] if name and name.isalpha()]
    
    if not is_valid_name(parent):
        if parent.lower() == 'who':
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"
    
    for child in children:
        if not is_valid_name(child):
            if child.lower() == 'who':
                return "Invalid name! 'Who' is a reserved word for questions."
            return "Names should only contain letters and cannot be reserved words!"
        if not safe_prolog_query(f"parent({parent}, {child})"):
            return "No."
    return "Yes!"

def handle_yesno_parents(match):
    """Handle 'Are X and Y the parents of Z?'"""
    a, b, c = match.groups()
    a, b, c = a.lower(), b.lower(), c.lower()
    
    if not all(is_valid_name(name) for name in [a, b, c]):
        if 'who' in [a.lower(), b.lower(), c.lower()]:
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"
    
    is_a_parent = bool(safe_prolog_query(f"father({a}, {c})")) or bool(safe_prolog_query(f"mother({a}, {c})"))
    
    is_b_parent = bool(safe_prolog_query(f"father({b}, {c})")) or bool(safe_prolog_query(f"mother({b}, {c})"))
    
    return "Yes!" if (is_a_parent and is_b_parent) else "No."

def handle_yesno_two_children(match):
    """Handle 'Are X and Y children of Z?'"""
    child1, child2, parent = match.groups()
    child1, child2, parent = child1.lower(), child2.lower(), parent.lower()
    
    if not all(is_valid_name(name) for name in [child1, child2, parent]):
        if 'who' in [child1.lower(), child2.lower(), parent.lower()]:
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"
    
    # Check if both are children of the parent
    result1 = safe_prolog_query(f"parent({parent}, {child1})")
    result2 = safe_prolog_query(f"parent({parent}, {child2})")
    
    return "Yes!" if (result1 and result2) else "No."

def handle_who_married_to(match):
    """Handle 'Who is X married to?'"""
    person = match.groups()[0].lower()
    
    if not is_valid_name(person):
        if person.lower() == 'who':
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"
    
    result = safe_prolog_query(f"married({person}, X)")
    names = {r["X"] for r in result if "X" in r}
    
    if names:
        return ", ".join(name.capitalize() for name in sorted(names))
    else:
        return "No one found."

def handle_who_spouse(match):
    """Handle 'Who is the spouse of X?'"""
    person = match.groups()[0].lower()
    
    if not is_valid_name(person):
        if person.lower() == 'who':
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"
    
    result = safe_prolog_query(f"spouse({person}, X)")
    names = {r["X"] for r in result if "X" in r}
    
    if names:
        return ", ".join(name.capitalize() for name in sorted(names))
    else:
        return "No one found."
    
def handle_list_query(match):
    rel, name = match.groups()
    name = name.lower()
    rel = rel.lower()
    
    if not is_valid_name(name):
        if name.lower() == 'who':
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"
    
    # Convert plurals to singular for Prolog queries
    plural_to_singular = {
        'siblings': 'sibling',
        'brothers': 'brother', 
        'sisters': 'sister',
        'children': 'child',
        'parents': 'parent',
        'sons': 'son',
        'daughters': 'daughter',
        'uncles': 'uncle',
        'aunts': 'aunt',
        'nephews': 'nephew',
        'nieces': 'niece',
        'cousins': 'cousin'
    }

    # Special case for "parents" - need to find all parents
    if rel == "parents":
        # Query for both fathers and mothers (includes step-parents through marriage)
        fathers = safe_prolog_query(f"father(X, {name})")
        mothers = safe_prolog_query(f"mother(X, {name})")
        
        father_names = {r["X"] for r in fathers if "X" in r}
        mother_names = {r["X"] for r in mothers if "X" in r}
        
        all_parents = father_names.union(mother_names)
        
        if all_parents:
            return ", ".join(name.capitalize() for name in sorted(all_parents))
        else:
            return "No one found."
    # Convert to singular if it's a plural form
    if rel in plural_to_singular:
        rel = plural_to_singular[rel]
    
    # Use the enhanced typo correction
    corrected_rel = correct_relationship_typo(rel)
    
    if corrected_rel is None:
        return f"I don't recognize the relationship '{rel}'. Try using common family relationships."
    
    rel = corrected_rel
    
    # Special case for children
    if rel == 'child':
        query = f"child(X, {name})"
    else:
        query = f"{rel}(X, {name})"
    
    result = safe_prolog_query(query)
    names = {r["X"] for r in result if "X" in r}
    
    if names:
        return ", ".join(name.capitalize() for name in sorted(names))
    else:
        return "No one found."

def handle_has_relation_question(match):
    person, relation, named_person = match.groups()
    person = person.lower()
    relation = relation.lower()
    
    if not is_valid_name(person):
        if person.lower() == 'who':
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"
    
    if named_person:
        named_person = named_person.lower()
        if not is_valid_name(named_person):
            if named_person.lower() == 'who':
                return "Invalid name! 'Who' is a reserved word for questions."
            return "Names should only contain letters and cannot be reserved words!"
        
        # Check if the specific person has that relation
        corrected_relation = correct_relationship_typo(relation)
        if corrected_relation is None:
            return f"I don't recognize the relationship '{relation}'. Try using common family relationships."
        
        result = safe_prolog_query(f"{corrected_relation}({named_person}, {person})")
        return "Yes!" if result else "No."
    else:
        # Check if person has any relation of that type
        corrected_relation = correct_relationship_typo(relation)
        if corrected_relation is None:
            return f"I don't recognize the relationship '{relation}'. Try using common family relationships."
        
        result = safe_prolog_query(f"{corrected_relation}(X, {person})")
        return "Yes!" if result else "No."

def handle_count_question(match):
    relation, person = match.groups()
    person = person.lower()
    relation = relation.lower()
    
    if not is_valid_name(person):
        if person.lower() == 'who':
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"
    
    # Use the enhanced typo correction
    corrected_relation = correct_relationship_typo(relation)
    
    if corrected_relation is None:
        return f"I don't recognize the relationship '{relation}'. Try using common family relationships."
    
    relation = corrected_relation
    result = safe_prolog_query(f"{relation}(X, {person})")
    count = len(result)
    return f"{count}"

def handle_relative_question(match):
    a, b = match.groups()
    a, b = a.lower(), b.lower()
    
    if not is_valid_name(a) or not is_valid_name(b):
        if a.lower() == 'who' or b.lower() == 'who':
            return "Invalid name! 'Who' is a reserved word for questions."
        return "Names should only contain letters and cannot be reserved words!"
    
    result = safe_prolog_query(f"relative({a}, {b})")
    return "Yes!" if result else "No."

# === Main Loop ===

def main():
    print("Welcome to the Family Chatbot!")
    print("Type your statement or question. Type 'exit' to quit.")
    print("Examples:")
    print("  - Bob is the father of Alice")
    print("  - Is Alice a daughter of Bob?")
    print("  - Who are the children of Bob?")
    print()
    
    while True:
        try:
            prompt = input("> ").strip()
            if prompt.lower() in ["exit", "quit", "bye", "goodbye"]:
                print("Goodbye!")
                break
            
            if not prompt:
                print("Bot: Please say something!")
                continue
                
            if prompt.endswith("?"):
                print("Bot:", parse_question(prompt))
            else:
                print("Bot:", parse_statement(prompt))
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Bot: Sorry, I encountered an unexpected error: {str(e)}")

if __name__ == "__main__":
    main()