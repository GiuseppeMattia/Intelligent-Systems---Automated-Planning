connected(S1, S2) :- stop(_, T, S1, X, _), stop(_, T, S2, Y, _), Y = X + 1, S1 != S2.

#show connected/2.