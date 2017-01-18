import nengo
import numpy as np


def UsherMcClelland(d, n_neurons, dt):
    k = 1.
    beta = 1.
    tau_model = 0.1

    tau_actual = 0.1

    # eqn (4) ignoring truncation, put into the canonical form:
    #   x[t+dt] = Ax[t] + Bu
    inhibit = np.ones((d, d))
    inhibit[np.diag_indices(d)] = 0.
    I = np.eye(d)
    B = 1. / tau_model
    A = (-k * I - beta * inhibit) / tau_model

    with nengo.Network() as net:
        net.input = nengo.Node(size_in=d)
        x = nengo.networks.EnsembleArray(
            n_neurons, d,
            eval_points=nengo.dists.Uniform(0., 1.),
            intercepts=nengo.dists.Uniform(0., 1.),
            encoders=nengo.dists.Choice([[1.]]))
        nengo.Connection(x.output, x.input, transform=tau_actual * A + I,
                         synapse=tau_actual)

        nengo.Connection(
            net.input, x.input,
            transform=tau_actual * B,
            synapse=tau_actual)

        net.output = x.output

    return net


def DriftDiffusion(d, n_neurons, dt, share_thresholding_intercepts=False):
    k = 0.
    beta = 0.
    tau_model = 0.1

    tau_actual = 0.1

    # eqn (4) ignoring truncation, put into the canonical form:
    #   x[t+dt] = Ax[t] + Bu
    inhibit = np.ones((d, d))
    inhibit[np.diag_indices(d)] = 0.
    I = np.eye(d)
    B = 1.0 / tau_model
    A = (-k * I - beta * inhibit) / tau_model

    n_neurons_threshold = 50
    n_neurons_x = n_neurons - n_neurons_threshold
    assert n_neurons_x > 0
    threshold = 0.8

    with nengo.Network() as net:
        net.input = nengo.Node(size_in=d)
        x = nengo.networks.EnsembleArray(
            n_neurons_x, d,
            eval_points=nengo.dists.Uniform(0., 1.),
            intercepts=nengo.dists.Uniform(0., 1.),
            encoders=nengo.dists.Choice([[1.]]))
        net.x = x
        nengo.Connection(x.output, x.input, transform=tau_actual * A + I,
                         synapse=tau_actual)

        nengo.Connection(
            net.input, x.input,
            transform=tau_actual * B,
            synapse=tau_actual)

        with nengo.presets.ThresholdingEnsembles(0.):
            thresholding = nengo.networks.EnsembleArray(n_neurons_threshold, d)
            if share_thresholding_intercepts:
                for e in thresholding.ensembles:
                    e.intercepts = nengo.dists.Exponential(
                        0.15, 0., 1.).sample(n_neurons_threshold)
            net.output = thresholding.add_output('heaviside', lambda x: x > 0.)

        bias = nengo.Node(1.)

        nengo.Connection(x.output, thresholding.input, synapse=0.005)
        nengo.Connection(
            bias, thresholding.input, transform=-threshold * np.ones((d, 1)))
        nengo.Connection(
            thresholding.heaviside, x.input,
            transform=-2. + 3. * np.eye(d), synapse=tau_actual)

    return net
