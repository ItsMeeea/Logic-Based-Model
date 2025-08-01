% === Base Facts (initially empty) ===
:- dynamic male/1.
:- dynamic female/1.
:- dynamic parent/2.
:- dynamic father/2.
:- dynamic mother/2.
:- dynamic son/2.
:- dynamic daughter/2.
:- dynamic brother/2.
:- dynamic sister/2.
:- dynamic sibling/2.
:- dynamic grandfather/2.
:- dynamic grandmother/2.
:- dynamic uncle/2.
:- dynamic aunt/2.
:- dynamic grandparent/2.

% === Gender & Parent Base Rules ===
father(F, C) :- male(F), parent(F, C).
mother(M, C) :- female(M), parent(M, C).

son(C, P) :- male(C), parent(P, C).
daughter(C, P) :- female(C), parent(P, C).

sibling(X, Y) :- parent(P, X), parent(P, Y), X \= Y.
brother(B, S) :- male(B), sibling(B, S).
sister(S, B) :- female(S), sibling(S, B).

% Grandparent relationships
grandparent(G, C) :- parent(G, P), parent(P, C).

grandfather(G, C) :- male(G), grandparent(G, C).
grandmother(G, C) :- female(G), grandparent(G, C).

% Uncle and aunt relationships
uncle(U, N) :- male(U), sibling(U, P), parent(P, N).
aunt(A, N) :- female(A), sibling(A, P), parent(P, N).

% Reverse definitions
child(C, P) :- parent(P, C).
% children(CList, P) :- forall(member(C, CList), parent(P, C)).

% Ancestor relationship (for detecting cycles)
ancestor(A, D) :- parent(A, D).
ancestor(A, D) :- parent(A, X), ancestor(X, D).

% Relative definition (common family members)
relative(X, Y) :- parent(X, Y).
relative(X, Y) :- parent(Y, X).
relative(X, Y) :- sibling(X, Y).
relative(X, Y) :- grandparent(X, Y).
relative(X, Y) :- grandparent(Y, X).
relative(X, Y) :- uncle(X, Y).
relative(X, Y) :- aunt(X, Y).
relative(X, Y) :- uncle(Y, X).
relative(X, Y) :- aunt(Y, X).

% Rule to check for gender conflicts (called explicitly, not as constraint)
gender_conflict(X) :- male(X), female(X).

% Helper predicates for validation
% valid_name(X) :- atom(X), atom_length(X, L), L > 0.

% Loop prevention
% impossible(parent(X, X)).
% impossible(ancestor(X, X)).

% Prevent impossible age relationships (simplified)
% impossible_age(grandfather(X, Y), father(Y, X)).
% impossible_age(grandmother(X, Y), mother(Y, X)).