from pyswip import Prolog

def parse_input(user_input):
    # TODO: error checking
    input_words = user_input.split()

    if(input_words[0] == "Who"):
        relationship = input_words[3]
        name = input_words[5][:-1]
        return ["Who", relationship, name]
    
    elif(input_words[0] == "Is"):
        name1 = input_words[1]
        name2 = input_words[5][:-1]
        relationship = input_words[3]
        return ["Q", relationship, name1, name2]
    
    elif(input_words[0] == "Are"):
        name1 = input_words[1]
        name2 = input_words[3]
        if(input_words[4][:-1] == "siblings"):
            return ["Q", "siblings", name1, name2]
        elif(input_words[4][:-1] == "relative"):
            return ["Q", "relatives", name1, name2]
        elif(input_words[4] == "the"):
            name3 = input_words[7][:-1]
            return ["Q", "parents", name1, name2, name3]
        elif(input_words[-3] == "children"):
            parent = input_words[-1][:-1]
            idx = input_words.index("and")
            children_list = user_input.split(", ")
            children_list = children_list[1:-1]
            children_list.append(input_words[idx - 1])
            children_list.append(input_words[idx + 1])
            family = ["Q", "children", idx + 1, parent]
            family.extend(children_list)
            return family
    
    if(input_words[1] == "is"):
        name1 = input_words[0]
        name2 = input_words[5][:-1]
        relationship = input_words[3]
        return [relationship, name1, name2]

    elif(input_words[-3] == "children"):
        parent = input_words[-1][:-1]
        idx = input_words.index("and")
        children_list = user_input.split(", ")
        children_list = children_list[:-1]
        children_list.append(input_words[idx - 1])
        children_list.append(input_words[idx + 1])
        family = ["children", idx + 1, parent]
        family.extend(children_list)
        return family
    
    elif(input_words[1] == "and"):
        name1 = input_words[0]
        name2 = input_words[2]
        if(input_words[4] == "the"):
            name3 = input_words[7][:-1]
            return ["parents", name1, name2, name3]
        else:
            return ["siblings", name1, name2]

def process_facts(keywords):
    # TODO check for contradictions (2 parents only, 4 grandparents only)
    fact = ""
    match keywords[0]:
        case "siblings":
            fact = f"sibling('{keywords[1]}', '{keywords[2]}').\n"
        case "parents":
            fact = f"parent('{keywords[1]}', '{keywords[3]}').\nparent('{keywords[2]}', '{keywords[3]}').\n"
        case "children":
            for i in range(3, keywords[1] + 3):
                fact += f"child('{keywords[i]}', '{keywords[2]}').\n"
        case _:
            fact = f"{keywords[0]}('{keywords[1]}', '{keywords[2]}').\n"
    
    with open("knowledge_base.pl", "a") as f:
        f.write(fact)

def process_questions(keywords):
    prolog = Prolog()
    prolog.consult("knowledge_base.pl")

    query = ""

    if(keywords[0] == "Q"):
        match(keywords[1]):
            case "siblings":
                if(bool(list(prolog.query(f"sibling('{keywords[2]}', '{keywords[3]}')")))):
                    return "Yes"
            case "parents":
                if(bool(list(prolog.query(f"parent('{keywords[2]}', '{keywords[4]}')"))) and bool(list(prolog.query(f"parent('{keywords[3]}', '{keywords[4]}')")))):
                    return "Yes"
            case "children":
                for i in range(4, keywords[2] + 3):
                    query += f"child('{keywords[i]}', '{keywords[3]}'), "
                query += f"child('{keywords[i]}', '{keywords[3]}')."
                if(bool(list(prolog.query(query)))):
                    return "Yes"
            case "relatives":
                if(bool(list(prolog.query(f"relative('{keywords[2]}', '{keywords[3]}')")))):
                    return "Yes"
            case _:
                if(bool(list(prolog.query(f"{keywords[1]}('{keywords[2]}', '{keywords[3]}')")))):
                    return "Yes"

    if(keywords[0] == "Who"):
        match(keywords[1]):
            case "mother":
                result = list(prolog.query(f"mother(X, '{keywords[2]}')"))
                result_list = [r['X'] for r in result]
                return ", ".join(result_list)
            case "father":
                result = list(prolog.query(f"father(X, '{keywords[2]}')"))
                result_list = [r['X'] for r in result]
                return ", ".join(result_list)
            case "children":
                result = list(prolog.query(f"child(X, '{keywords[2]}')"))
                result_list = [r['X'] for r in result]
                return ", ".join(result_list)
            case _:
                result = list(prolog.query(f"{keywords[1][:-1]}(X, '{keywords[2]}')"))
                result_list = [r['X'] for r in result]
                return ", ".join(result_list)
    return None # TODO fix for error checkin

def encode_rules():
    # TODO ayusin pag may kulang
    # siblings share at least one parent daw
    # mali ang mother :- parent
    # fyi mali pag lagay both parent:child and child:parent

    rules = r"""sibling(Z, Y) :- parent(X, Y), child(Z, X).
parent(X, Y) :- child(Y, X).
relative(X, Y) :- sibling(X, Y).
relative(X, Y) :- parent(X, Y).
relative(X, Y) :- child(X, Y).
relative(X, Y) :- grandmother(X, Y).
relative(X, Y) :- grandfather(X, Y).
relative(X, Y) :- aunt(X, Y).
relative(X, Y) :- uncle(X, Y).
"""

    """
    sibling(X, Y) :- sister(X, Y).
    sibling(X, Y) :- brother(X, Y).
    parent(X, Y) :- mother(X, Y).
    parent(X, Y) :- father(X, Y).
    parent(X, Y) :- daughter(Y, X).
    parent(X, Y) :- son(Y, X).
    uncle(Z, Y) :- grandmother(X, Y), son(Z, X).
    uncle(Z, Y) :- grandfather(X, Y), son(Z, X).
    uncle(Z, Y) :- parent(X, Y), brother(Z, X).
    aunt(Z, Y) :- grandmother(X, Y), daughter(Z, X).
    aunt(Z, Y) :- grandfather(X, Y), daughter(Z, X).
    aunt(Z, Y) :- parent(X, Y), sister(Z, X).
    grandmother(Z, Y) :- parent(X, Y), mother(Z, X).
    grandfather(Z, Y) :- parent(X, Y), father(Z, X).
    child(X, Y) :- mother(Y, X).
    child(X, Y) :- father(Y, X).
    child(X, Y) :- daughter(X, Y).
    child(X, Y) :- son(X, Y).
    """
    with open("knowledge_base.pl", "w") as f:
            f.write(rules)

def main():
    encode_rules()

    while True:
        # REMOVE THIS PART ONLY LATER FOR GUI-----
        user_input = input("Enter sample input: ")
        # -----------------------------------------

        keywords = parse_input(user_input)


        if(keywords[0] == "Q" or keywords[0] == "Who"):
            answer = process_questions(keywords)
            # REMOVE THIS PART ONLY LATER FOR GUI-----
            print(answer)
            # -----------------------------------------
        else:
            process_facts(keywords)

if __name__ == "__main__":
    main()