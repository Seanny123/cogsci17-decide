import nengo
import numpy as np


def UsherMcClelland(d, n_neurons, dt):
    k = 1.
    beta = 1.
    tau_model = 0.01

    tau_actual = 0.1
    a = np.exp(-dt / tau_actual)

    # eqn (4) ignoring truncation, put into the canonical form:
    #   x[t+dt] = Ax[t] + Bu
    inhibit = np.ones((d, d))
    inhibit[np.diag_indices(d)] = 0.
    I = np.eye(d)
    B = dt / tau_model
    A = (-k * I - beta * inhibit) * dt / tau_model + I

    with nengo.Network() as net:
        net.input = nengo.Node(size_in=d)
        x = nengo.Ensemble(d * n_neurons, d)

        for i in range(d):
            nengo.Connection(
                net.input[i], x[i],
                transform=B / (1 - a),  # discrete principle 3
                synapse=tau_actual)

        nengo.Connection(
            x, x, transform=(A - a * I) / (1 - a),  # discrete principle 3
            synapse=tau_actual)

        net.output = x

    return net


def DriftDiffusion(d, n_neurons, dt):
    k = 0.
    beta = 0.
    tau_model = 0.01

    tau_actual = 0.1
    a = np.exp(-dt / tau_actual)

    # eqn (4) ignoring truncation, put into the canonical form:
    #   x[t+dt] = Ax[t] + Bu
    inhibit = np.ones((d, d))
    inhibit[np.diag_indices(d)] = 0.
    I = np.eye(d)
    B = dt / tau_model
    A = (-k * I - beta * inhibit) * dt / tau_model + I

    n_neurons_threshold = 50
    n_neurons_x = n_neurons - n_neurons_threshold
    assert n_neurons_x > 0
    threshold = 0.8

    with nengo.Network() as net:
        net.input = nengo.Node(size_in=d)
        x = nengo.Ensemble(d * n_neurons, d)

        for i in range(d):
            nengo.Connection(
                net.input[i], x[i],
                transform=B / (1 - a),  # discrete principle 3
                synapse=tau_actual)

        nengo.Connection(
            x, x, transform=(A - a * I) / (1 - a),  # discrete principle 3
            synapse=tau_actual)

        with nengo.presets.ThresholdingEnsembles(0.):
            thresholding = nengo.networks.EnsembleArray(n_neurons, d)
            net.output = thresholding.add_output('heaviside', lambda x: x > 0.)

        bias = nengo.Node(1.)

        nengo.Connection(x, thresholding.input)
        nengo.Connection(
            bias, thresholding.input, transform=-threshold * np.ones((d, 1)))
        nengo.Connection(
            thresholding.heaviside, x,
            transform=-2. + 2.5 * np.eye(d) / (1 - a), synapse=tau_actual)

    return net
