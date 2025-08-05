% === Base Facts (initially empty) ===
:- dynamic male/1.
:- dynamic female/1.
:- dynamic parent/2.
:- dynamic married/2.
:- dynamic grandparent/2.
:- dynamic uncle/2.
:- dynamic aunt/2.
:- dynamic nephew/2.   
:- dynamic niece/2.     
:- dynamic cousin/2.
:- dynamic sibling_deferred/2.

:- table father/2.
:- table mother/2.

% === Gender & Parent Base Rules ===
% Father is a male parent OR male married to someone who is a parent
father(F, C) :- male(F), parent(F, C).
father(F, C) :- male(F), married(F, M), parent(M, C).
father(F, C) :- male(F), married(M, F), parent(M, C).

% Mother is a female parent OR female married to someone who is a parent
mother(M, C) :- female(M), parent(M, C).
mother(M, C) :- female(M), married(M, F), parent(F, C).
mother(M, C) :- female(M), married(F, M), parent(F, C).

son(C, P) :- male(C), parent(P, C).
son(C, P) :- male(C), father(P, C).
son(C, P) :- male(C), mother(P, C).

daughter(C, P) :- female(C), parent(P, C).
daughter(C, P) :- female(C), father(P, C).
daughter(C, P) :- female(C), mother(P, C).

sibling(X, Y) :- parent(P, X), parent(P, Y), X \= Y.
sibling(X, Y) :- father(P, X), father(P, Y), X \= Y.
sibling(X, Y) :- mother(P, X), mother(P, Y), X \= Y.
sibling(X, Y) :- sibling_deferred(X, Y).

brother(B, S) :- male(B), sibling(B, S).
sister(S, B) :- female(S), sibling(S, B).

% Grandparent relationships
grandparent(G, C) :- parent(G, P), parent(P, C).
grandparent(G, C) :- parent(G, P), father(P, C).
grandparent(G, C) :- parent(G, P), mother(P, C).
grandparent(G, C) :- father(G, P), parent(P, C).
grandparent(G, C) :- mother(G, P), parent(P, C).

grandfather(G, C) :- male(G), grandparent(G, C).
grandmother(G, C) :- female(G), grandparent(G, C).

grandchild(GC, GP) :- grandparent(GP, GC).
grandson(GS, GP) :- male(GS), grandparent(GP, GS).
granddaughter(GD, GP) :- female(GD), grandparent(GP, GD).

% Uncle and aunt relationships
uncle(U, N) :- male(U), sibling(U, P), parent(P, N).
uncle(U, N) :- male(U), sibling(U, P), father(P, N).
uncle(U, N) :- male(U), sibling(U, P), mother(P, N).

aunt(A, N) :- female(A), sibling(A, P), parent(P, N).
aunt(A, N) :- female(A), sibling(A, P), father(P, N).
aunt(A, N) :- female(A), sibling(A, P), mother(P, N).

% Nephew and niece relationships (reverse of uncle/aunt)
nephew(N, UA) :- male(N), uncle(UA, N).
nephew(N, UA) :- male(N), aunt(UA, N).

niece(N, UA) :- female(N), uncle(UA, N).
niece(N, UA) :- female(N), aunt(UA, N).

% Cousin relationships (children of siblings)
cousin(C1, C2) :- 
    parent(P1, C1), 
    parent(P2, C2), 
    sibling(P1, P2), 
    C1 \= C2.
cousin(C1, C2) :- 
    father(P1, C1), 
    father(P2, C2), 
    sibling(P1, P2), 
    C1 \= C2.
cousin(C1, C2) :- 
    mother(P1, C1), 
    mother(P2, C2), 
    sibling(P1, P2), 
    C1 \= C2.

% Marriage relationships
husband(H, W) :- male(H), married(H, W).
husband(H, W) :- male(H), married(W, H).

wife(W, H) :- female(W), married(W, H).
wife(W, H) :- female(W), married(H, W).

spouse(X, Y) :- married(X, Y).
spouse(X, Y) :- married(Y, X).

% Reverse definitions
child(C, P) :- parent(P, C).
child(C, P) :- father(P, C).
child(C, P) :- mother(P, C).

% Ancestor relationship (for detecting cycles)
ancestor(A, D) :- parent(A, D).
ancestor(A, D) :- parent(A, X), ancestor(X, D).

% Enhanced relative definition
relative(X, Y) :- parent(X, Y).
relative(X, Y) :- parent(Y, X).
relative(X, Y) :- father(X, Y).
relative(X, Y) :- father(Y, X).
relative(X, Y) :- mother(X, Y).
relative(X, Y) :- mother(Y, X).
relative(X, Y) :- sibling(X, Y).
relative(X, Y) :- grandparent(X, Y).
relative(X, Y) :- grandparent(Y, X).
relative(X, Y) :- grandchild(X, Y).
relative(X, Y) :- grandchild(Y, X).
relative(X, Y) :- grandson(X, Y).
relative(X, Y) :- grandson(Y, X).
relative(X, Y) :- granddaughter(X, Y).
relative(X, Y) :- granddaughter(Y, X).
relative(X, Y) :- uncle(X, Y).
relative(X, Y) :- aunt(X, Y).
relative(X, Y) :- uncle(Y, X).
relative(X, Y) :- aunt(Y, X).
relative(X, Y) :- nephew(X, Y).    
relative(X, Y) :- niece(X, Y).    
relative(X, Y) :- nephew(Y, X).    
relative(X, Y) :- niece(Y, X).     
relative(X, Y) :- cousin(X, Y).    
relative(X, Y) :- married(X, Y).
relative(X, Y) :- married(Y, X).
relative(X, Y) :- spouse(X, Y).

% Rule to check for gender conflicts
gender_conflict(X) :- male(X), female(X).