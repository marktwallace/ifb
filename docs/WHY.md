### Bits only

Ever since I first heard Wheeler’s expression, “it from bit,” I’ve wanted to write a simulator for that. I might not know much QFT, but I do know bits.

Recently I was listening to Sean Carroll interview Leonard Susskind, and it got me thinking (again) about infinities in physics — and how much I wish there were a simpler way to model things like the Holographic Principle. So I’m trying to write a model in the simplest possible way, in PyTorch. No infinities, no infinitesimals, no floating point. Everything is discrete.

I don’t believe in the real number line. That’s not as extreme as it sounds. Even Hilbert, late in life, leaned toward the idea that infinities aren’t physical and that a discrete approach might make more philosophical sense. Also, I think QFT is too hard — and if I’m not using the real number line, then I don’t get calculus, and therefore I wouldn’t be using QFT anyway.

#### What this model is

I’m doing what feels like the most obvious thing: I’m using Standard Model particles — nothing beyond that — and sticking to leptons and photons for now. I want to model large-scale entanglement, but I’m honestly a little scared of protons (maybe I watched The Three-Body Problem one too many times), so I’m starting with a muonium cloud, similar in spirit to the old QED precision experiments.

The goal is to see whether space and time — and therefore things like position and momentum — can emerge from the entanglement structure itself. The core object is an entanglement graph, represented as a DAG (Directed Acyclic Graph), mainly for computational efficiency. I need updates to proceed in a definite order without getting trapped in loops.

In this graph:

Nodes = Standard Model particles

Edges = entanglement relationships

And I’m keeping it extremely minimal: an entanglement is just one bit — two particles are either entangled with respect to spin, or they’re not. No amplitudes, no continuous phases, no density matrices yet.

#### Why the DAG and the update rules are simple

The DAG is not a claim about how the universe “really” works. It’s just a practical way to run updates without infinite recursion or circular dependencies. It’s bookkeeping.

The update rules — the rules for when entanglements form, persist, or break — are deliberately naive at this stage. The only constraint I’m respecting is that they should not violate the Standard Model. No illegal interactions, no forbidden spin configurations, no conservation-law violations. Beyond that, they’re just an initial guess that lets the system run.

#### What I am not doing

I have not gone deep into other emergent-space or discrete models — not because I think they’re wrong, but because I want to avoid cheating. If I start with qubits, or Hilbert spaces, or any structure that already assumes continuous amplitudes or geometry, then I’ve basically smuggled space and time into the model from the start. That defeats the point.

So I’m intentionally keeping everything as bare and dumb and transparent as possible. If something interesting — like locality, spatial structure, or time-like ordering — does appear, I want to be able to say confidently that it emerged, and wasn’t hiding inside a fancy data type from line one.

### What do I hope to accomplish?

This is a serious attempt to get “it” from only bits. Meaning: any property of a particle (or of the system as a whole) that normally has a real or complex value should, in this model, emerge from simpler interactions that are just yes/no. No amplitudes, no continuous parameters. Just discrete relationships — like the phase-free entanglement edges in the DAG.

In the very crude resolution of this model, I’m not even sure that causality (one particle emitting another) will look different from entanglement. Both may just show up as edges in the DAG. You can think of the DAG a little like this: a universe where Feynman diagrams are the only real objects, but there are no continuous amplitudes silently riding on top of them.

Position, momentum, energy, mass — all of that has to emerge, or it doesn’t exist in the model. Do I think I’ll actually get all the way there? Of course not. For all I know, something like momentum might only emerge for systems of 10^20 or 10^30 particles. And gravity probably needs far, far more than that to show anything recognizable.

On a GPU, I can probably simulate something like a million edges, and maybe, with a lot of work, a billion. That’s nowhere close to Avogadro’s number. So I am not expecting full physics to fall out here.

But I am interested in whether any hint of these ideas shows up — even faint traces of locality, transport behavior, or something that acts like a conserved quantity. I take existing physics very seriously; the Standard Model and gravity are the ground truths here. I’m not trying to replace them. I just want to see whether something vaguely similar can emerge from a completely different starting point — one that is purely discrete, with no hidden real numbers anywhere.

And I’m enjoying thinking it through.
