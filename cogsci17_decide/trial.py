import nengo
import numpy as np
import pytry

import cogsci17_decide.networks


class DecisionTrial(pytry.NengoTrial):
    def params(self):
        self.param("network under test", network='UsherMcClelland')
        self.param("# choices", d=10)
        self.param("# neurons per choice", N=200)

        self.param("input baseline", baseline=0.1)
        self.param("target separation", target_sep=0.2)
        self.param("noise std", noise=0.)

    def model(self, p):
        with nengo.Network(seed=p.seed) as model:
            decide = getattr(cogsci17_decide.networks, p.network)(
                d=p.d, n_neurons=p.N, dt=p.dt)

            stimulus = p.baseline * np.ones(p.d)
            stimulus[0] += p.target_sep
            stimulus_node = nengo.Node(stimulus)
            nengo.Connection(stimulus_node, decide.input, synapse=None)

            if p.noise > 0.:
                noise_node = nengo.Node(nengo.processes.WhiteNoise(
                    nengo.dists.Gaussian(.0, p.noise)), size_out=p.d)
            else:
                noise_node = nengo.Node(np.zeros(p.d))
            nengo.Connection(noise_node, decide.input, synapse=None)

            self.probe = nengo.Probe(decide.output, synapse=0.01)
        return model

    def evaluate(self, p, sim, plt):
        sim.run(1.)

        if plt is not None:
            plt.plot(sim.trange(), sim.data)
            plt.xlabel("Time [s]")

        ss_data = sim.data[self.probe][sim.trange() > 0.5, :]
        smoothed = np.mean(ss_data, axis=0)
        winner = np.argmax(smoothed)
        mask = np.ones(p.d, dtype=bool)
        mask[winner] = False
        runnerup = np.argmax(smoothed[mask])
        if runnerup >= winner:
            runnerup += 1

        correct = np.all(
            np.argmax(ss_data, axis=1) == 0) and smoothed[0] > 0.1,
        t = np.nan
        if correct:
            risen = np.flatnonzero(
                sim.data[self.probe][:, winner] > 1. - 1. / np.e)
            if len(risen) > 0:
                fall = np.flatnonzero(
                    sim.data[self.probe][:, runnerup] > 1. / np.e)
                idx = risen[0]
                if np.any(fall > idx):
                    idx = fall[-1]
                if idx >= len(sim.trange() - 1):
                    t = np.nan
                else:
                    t = sim.trange()[idx]

        return dict(
            correct=correct,
            t=t,
            winner_err=np.max(smoothed) - 1.,
            runnerup_err=max(0., np.max(smoothed[mask])),
            runnerup_highest_err=max(0., np.max(sim.data[self.probe][:, mask]))
        )