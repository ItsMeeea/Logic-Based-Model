from pyswip import Prolog
import re
from pyswip.prolog import PrologError

prolog = Prolog()
prolog.consult("family.pl")

def assert_once(fact):
    """Assert a fact only if it doesn't already exist"""
    try:
        if not list(prolog.query(fact)):
            prolog.assertz(fact)
        return True
    except PrologError:
        return False

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

def check_circular_ancestry(person, ancestor):
    """Check if making person a descendant of ancestor would create a cycle"""
    person, ancestor = person.lower(), ancestor.lower()
    
    if person == ancestor:
        return True
    
    try:
        # Check if ancestor is already a descendant of person
        # This checks if there's already a path from person to ancestor
        result = list(prolog.query(f"ancestor({person}, {ancestor})"))
        if result:
            return True
            
        # Also check direct parent relationship in reverse
        result = list(prolog.query(f"parent({person}, {ancestor})"))
        if result:
            return True
            
        return False
    except PrologError:
        return False

def check_would_create_cycle(new_parent, new_child):
    """Check if adding parent(new_parent, new_child) would create a cycle"""
    new_parent, new_child = new_parent.lower(), new_child.lower()
    
    # Self-relation check
    if new_parent == new_child:
        return True
    
    try:
        # Check if new_child is already an ancestor of new_parent
        # If so, making new_parent a parent of new_child would create a cycle
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
                      'grandfather', 'grandmother', 'uncle', 'aunt', 'child', 'parent']
    
    # Step 1: Manual corrections for common typos
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
        'siblig': 'sibling'
    }
    
    if word in manual_corrections:
        return manual_corrections[word]
    
    # Step 2: Handle plural forms
    if word.endswith('s') and word[:-1] in valid_relations:
        return word[:-1]
    
    # Handle special case for children -> child
    if word == 'children':
        return 'child'
    
    # Step 3: Check exact match
    if word in valid_relations:
        return word
    
    # Step 4: Fuzzy matching with Levenshtein distance
    best_match = None
    best_distance = float('inf')
    threshold = 2  # Maximum allowed edit distance
    
    for valid_word in valid_relations:
        distance = levenshtein_distance(word, valid_word)
        if distance <= threshold and distance < best_distance:
            best_distance = distance
            best_match = valid_word
    
    return best_match

# === Statement Parsing ===

def parse_statement(prompt):
    prompt = prompt.strip().rstrip(".")
    
    # Handle empty input
    if not prompt:
        return "Please tell me something!"

    patterns = [
        (r"(\w+) is (?:a |an |the )?(father|mother|parent|child|son|daughter|brother|sister|sibling|uncle|aunt|grandfather|grandmother) of (\w+)", handle_single_relation),
        (r"(\w+) and (\w+) are siblings", handle_siblings),
        (r"(\w+) and (\w+) are (?:the )?parents of (\w+)", handle_parents),
        (r"(\w+), (\w+)(?:, and (\w+))? are children of (\w+)", handle_children),
        (r"(\w+) is (?:a |an |the )?child of (\w+)", handle_child_relation),
        # Handle some common variations
        (r"(\w+) has (?:a |an |the )?(son|daughter|child) (?:named )?(\w+)", handle_has_child),
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

from pyswip import Prolog
import re
from pyswip.prolog import PrologError

prolog = Prolog()
prolog.consult("family.pl")

def assert_once(fact):
    """Assert a fact only if it doesn't already exist"""
    try:
        if not list(prolog.query(fact)):
            prolog.assertz(fact)
        return True
    except PrologError:
        return False

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

def check_circular_ancestry(person, ancestor):
    """Check if making person a descendant of ancestor would create a cycle"""
    person, ancestor = person.lower(), ancestor.lower()
    
    if person == ancestor:
        return True
    
    try:
        # Check if ancestor is already a descendant of person
        # This checks if there's already a path from person to ancestor
        result = list(prolog.query(f"ancestor({person}, {ancestor})"))
        if result:
            return True
            
        # Also check direct parent relationship in reverse
        result = list(prolog.query(f"parent({person}, {ancestor})"))
        if result:
            return True
            
        return False
    except PrologError:
        return False

def check_would_create_cycle(new_parent, new_child):
    """Check if adding parent(new_parent, new_child) would create a cycle"""
    new_parent, new_child = new_parent.lower(), new_child.lower()
    
    # Self-relation check
    if new_parent == new_child:
        return True
    
    try:
        # Check if new_child is already an ancestor of new_parent
        # If so, making new_parent a parent of new_child would create a cycle
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
                      'grandfather', 'grandmother', 'uncle', 'aunt', 'child', 'parent']
    
    # Step 1: Manual corrections for common typos
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
        'siblig': 'sibling'
    }
    
    if word in manual_corrections:
        return manual_corrections[word]
    
    # Step 2: Handle plural forms
    if word.endswith('s') and word[:-1] in valid_relations:
        return word[:-1]
    
    # Handle special case for children -> child
    if word == 'children':
        return 'child'
    
    # Step 3: Check exact match
    if word in valid_relations:
        return word
    
    # Step 4: Fuzzy matching with Levenshtein distance
    best_match = None
    best_distance = float('inf')
    threshold = 2  # Maximum allowed edit distance
    
    for valid_word in valid_relations:
        distance = levenshtein_distance(word, valid_word)
        if distance <= threshold and distance < best_distance:
            best_distance = distance
            best_match = valid_word
    
    return best_match

# === Statement Parsing ===

def parse_statement(prompt):
    prompt = prompt.strip().rstrip(".")
    
    # Handle empty input
    if not prompt:
        return "Please tell me something!"

    patterns = [
        (r"(\w+) is (?:a |an |the )?(father|mother|parent|child|son|daughter|brother|sister|sibling|uncle|aunt|grandfather|grandmother) of (\w+)", handle_single_relation),
        (r"(\w+) and (\w+) are siblings", handle_siblings),
        (r"(\w+) and (\w+) are (?:the )?parents of (\w+)", handle_parents),
        (r"(\w+), (\w+)(?:, and (\w+))? are children of (\w+)", handle_children),
        (r"(\w+) is (?:a |an |the )?child of (\w+)", handle_child_relation),
        # Handle some common variations
        (r"(\w+) has (?:a |an |the )?(son|daughter|child) (?:named )?(\w+)", handle_has_child),
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

def get_parents(person):
    """Get all parents of a person"""
    result = safe_prolog_query(f"parent(P, {person})")
    return {r["P"] for r in result if "P" in r}

def handle_single_relation(match):
    a, rel, b = match.groups()
    a, b = a.lower(), b.lower()

    # Validate names (only letters)
    if not a.isalpha() or not b.isalpha():
        return "Names should only contain letters!"

    if check_self_relation(a, b):
        return "That's impossible!"

    # Determine gender based on relation
    if rel in ["father", "son", "brother", "uncle", "grandfather"]:
        gender = "male"
    elif rel in ["mother", "daughter", "sister", "aunt", "grandmother"]:
        gender = "female"
    else:
        gender = None  # parent, child, sibling don't specify gender
    
    # Check for contradictions (this will check if person already has opposite gender)
    if gender and check_contradiction(a, gender):
        return "That's impossible!"
    
    # Handle different relationship types
    if rel in ["father", "mother", "parent"]:
        if check_would_create_cycle(a, b):
            return "That's impossible!"
        # Assert parent relationship
        if not assert_once(f"parent({a}, {b})"):
            return "Error adding that relationship!"
    elif rel in ["son", "daughter", "child"]:
        if check_would_create_cycle(b, a):
            return "That's impossible!"
        # Assert parent relationship (b is parent of a)
        if not assert_once(f"parent({b}, {a})"):
            return "Error adding that relationship!"
    elif rel in ["brother", "sister", "sibling"]:
        # Handle sibling relationship with smart inference
        result = handle_sibling_with_smart_inference(a, b, rel)
        # IMPORTANT: Assert gender AFTER sibling handling
        if gender:
            assert_once(f"{gender}({a})")
        return result
    elif rel in ["grandfather", "grandmother"]:
        # Check for cycles in grandparent relationships
        if check_would_create_cycle(a, b):
            return "That's impossible!"
        # This means a is grandparent of b
        assert_once(f"grandparent({a}, {b})")
    elif rel in ["uncle", "aunt"]:
        # Record the direct relationship
        assert_once(f"{rel}({a}, {b})")

    # Assert gender after all checks pass
    if gender:
        assert_once(f"{gender}({a})")

    return "OK! I learned something."

def handle_sibling_with_smart_inference(person1, person2, rel):
    """Handle sibling relationships with automatic parent inference"""
    
    # Get existing parents for both people
    parents1 = get_parents(person1)
    parents2 = get_parents(person2)
    
    # Case 1: They already share at least one parent - they're already siblings
    shared_parents = parents1.intersection(parents2)
    if shared_parents:
        return "OK! I already knew they were siblings through their shared parent(s)."
    
    # Case 2: One has parents, the other doesn't - infer shared parentage
    if parents1 and not parents2:
        for parent in parents1:
            assert_once(f"parent({parent}, {person2})")
        parent_names = ', '.join(p.capitalize() for p in parents1)
        return "OK! I learned something."
    
    elif parents2 and not parents1:
        for parent in parents2:
            assert_once(f"parent({parent}, {person1})")
        parent_names = ', '.join(p.capitalize() for p in parents2)
        return "OK! I learned something."
    
    # Case 3: Neither has parents - ask for clarification
    elif not parents1 and not parents2:
        return f"To establish that {person1.capitalize()} and {person2.capitalize()} are siblings, I need to know who their parent(s) are. Could you tell me about their parents?"
    
    # Case 4: Both have different parents - ASSUME they share all parents (full siblings)
    else:
        # Auto-infer that they share all parents
        all_parents = parents1.union(parents2)
        for parent in all_parents:
            assert_once(f"parent({parent}, {person1})")
            assert_once(f"parent({parent}, {person2})")
        
        parent_names = ', '.join(p.capitalize() for p in all_parents)
        return f"OK! I learned that both {person1.capitalize()} and {person2.capitalize()} have {parent_names} as their parents, making them full siblings."

  
def handle_has_child(match):
    parent, child_type, child = match.groups()
    parent, child = parent.lower(), child.lower()
    
    if check_self_relation(parent, child):
        return "That's impossible!"
    
    if check_would_create_cycle(parent, child):
        return "That's impossible!"
    
    # Determine child's gender
    if child_type in ["son"]:
        assert_once(f"male({child})")
    elif child_type in ["daughter"]:
        assert_once(f"female({child})")
    
    assert_once(f"parent({parent}, {child})")
    return "OK! I learned something."

def handle_have_child(match):
    parent1, parent2, child = match.groups()
    parent1, parent2, child = parent1.lower(), parent2.lower(), child.lower()
    
    if child in [parent1, parent2]:
        return "That's impossible!"
    
    if check_would_create_cycle(parent1, child) or check_would_create_cycle(parent2, child):
        return "That's impossible!"
    
    assert_once(f"parent({parent1}, {child})")
    assert_once(f"parent({parent2}, {child})")
    return "OK! I learned something."

def handle_child_relation(match):
    child, parent = match.groups()
    child, parent = child.lower(), parent.lower()
    
    if not child.isalpha() or not parent.isalpha():
        return "Names should only contain letters!"
    
    if check_self_relation(child, parent):
        return "That's impossible!"
    
    if check_would_create_cycle(parent, child):
        return "That's impossible!"
    
    if not assert_once(f"parent({parent}, {child})"):
        return "Error adding that relationship!"
    return "OK! I learned something."

def handle_siblings(match):
    a, b = match.groups()
    a, b = a.lower(), b.lower()

    if not a.isalpha() or not b.isalpha():
        return "Names should only contain letters!"

    if check_self_relation(a, b):
        return "That's impossible!"

    # Use the same smart inference logic as handle_single_relation
    return handle_sibling_with_smart_inference(a, b, "sibling")

def handle_parents(match):
    a, b, c = match.groups()
    a, b, c = a.lower(), b.lower(), c.lower()

    if not all(name.isalpha() for name in [a, b, c]):
        return "Names should only contain letters!"

    if c in [a, b]:
        return "That's impossible!"
    
    if check_would_create_cycle(a, c) or check_would_create_cycle(b, c):
        return "That's impossible!"

    assert_once(f"parent({a}, {c})")
    assert_once(f"parent({b}, {c})")
    return "OK! I learned something."

def handle_children(match):
    groups = match.groups()
    parent = groups[-1].lower()
    children = [name.lower() for name in groups[:-1] if name and name.isalpha()]

    if not parent.isalpha():
        return "Names should only contain letters!"

    for child in children:
        if check_self_relation(child, parent):
            return "That's impossible!"
        if check_would_create_cycle(parent, child):
            return "That's impossible!"
        assert_once(f"parent({parent}, {child})")
    return "OK! I learned something."

# === Question Parsing ===

def parse_question(prompt):
    prompt = prompt.strip().rstrip("?")
    
    # Handle empty input
    if not prompt:
        return "What would you like to know?"

    patterns = [
        (r"Is (\w+) (?:a |an |the )?(\w+) of (\w+)", handle_yesno_relation),
        (r"Are (\w+) and (\w+) siblings", handle_yesno_sibling),
        (r"Are (\w+), (\w+)(?:, and (\w+))? children of (\w+)", handle_yesno_children),
        (r"Who (?:is|are) (?:the |a |an )?(\w+) of (\w+)", handle_list_query),
        (r"Are (\w+) and (\w+) relatives", handle_relative_question),
        # Handle some variations
        (r"Does (\w+) have (?:a |an |any )?(\w+)", handle_has_relation_question),
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
    if not a.isalpha() or not b.isalpha():
        return "Names should only contain letters!"
    
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
    
    if not a.isalpha() or not b.isalpha():
        return "Names should only contain letters!"
    
    result = safe_prolog_query(f"sibling({a}, {b})")
    return "Yes!" if result else "No."

def handle_yesno_children(match):
    groups = match.groups()
    parent = groups[-1].lower()
    children = [name.lower() for name in groups[:-1] if name and name.isalpha()]
    
    if not parent.isalpha():
        return "Names should only contain letters!"
    
    for child in children:
        if not safe_prolog_query(f"parent({parent}, {child})"):
            return "No."
    return "Yes!"

def handle_list_query(match):
    rel, name = match.groups()
    name = name.lower()
    rel = rel.lower()
    
    if not name.isalpha():
        return "Names should only contain letters!"
    
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
    person, relation = match.groups()
    person = person.lower()
    relation = relation.lower()
    
    if not person.isalpha():
        return "Names should only contain letters!"
    
    # Use the enhanced typo correction
    corrected_relation = correct_relationship_typo(relation)
    
    if corrected_relation is None:
        return f"I don't recognize the relationship '{relation}'. Try using common family relationships."
    
    relation = corrected_relation
    result = safe_prolog_query(f"{relation}(X, {person})")
    return "Yes!" if result else "No."

def handle_count_question(match):
    relation, person = match.groups()
    person = person.lower()
    relation = relation.lower()
    
    if not person.isalpha():
        return "Names should only contain letters!"
    
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
    
    if not a.isalpha() or not b.isalpha():
        return "Names should only contain letters!"
    
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
