"""The schema used by the sqlite database for storing the penalty models."""

schema = \
    """
    CREATE TABLE IF NOT EXISTS graph(
        num_nodes INTEGER NOT NULL,  -- for integer-labeled graphs, num_nodes encodes all of the nodes
        num_edges INTEGER NOT NULL,  -- redundant, allows for faster selects
        edges TEXT NOT NULL,  -- json list of lists, should be sorted (with each edge sorted)
        id INTEGER PRIMARY KEY,
        CONSTRAINT graph UNIQUE (
            num_nodes,
            edges));

    CREATE TABLE IF NOT EXISTS feasible_configurations(
        num_variables INTEGER NOT NULL,
        num_feasible_configurations INTEGER NOT NULL,
        feasible_configurations TEXT NOT NULL,
        energies TEXT NOT NULL,
        id INTEGER PRIMARY KEY,
        CONSTRAINT feasible_configurations UNIQUE (
            num_variables,
            num_feasible_configurations,
            feasible_configurations,
            energies));

    CREATE TABLE IF NOT EXISTS ising_model(
        linear_biases TEXT NOT NULL,
        quadratic_biases TEXT NOT NULL,
        offset REAL NOT NULL,
        max_quadratic_bias REAL NOT NULL,
        min_quadratic_bias REAL NOT NULL,
        max_linear_bias REAL NOT NULL,
        min_linear_bias REAL NOT NULL,
        graph_id INTEGER NOT NULL,
        id INTEGER PRIMARY KEY,
        CONSTRAINT ising_model UNIQUE (
            linear_biases,
            quadratic_biases,
            offset,
            graph_id),
        FOREIGN KEY (graph_id) REFERENCES graph(id) ON DELETE CASCADE);

    CREATE TABLE IF NOT EXISTS penalty_model(
        decision_variables TEXT NOT NULL,
        classical_gap REAL NOT NULL,
        ground_energy REAL NOT NULL,
        feasible_configurations_id INT,
        ising_model_id INT,
        id INTEGER PRIMARY KEY,
        FOREIGN KEY (feasible_configurations_id) REFERENCES feasible_configurations(id) ON DELETE CASCADE,
        FOREIGN KEY (ising_model_id) REFERENCES ising_model(id) ON DELETE CASCADE,
        CONSTRAINT ising_model UNIQUE (
            decision_variables,
            feasible_configurations_id,
            ising_model_id));

    CREATE VIEW IF NOT EXISTS penalty_model_view AS
    SELECT
        num_variables,
        num_feasible_configurations,
        feasible_configurations,
        energies,

        num_nodes,
        num_edges,
        edges,

        linear_biases,
        quadratic_biases,
        offset,
        max_quadratic_bias,
        min_quadratic_bias,
        max_linear_bias,
        min_linear_bias,

        decision_variables,
        classical_gap,
        ground_energy,
        penalty_model.id
    FROM
        ising_model,
        feasible_configurations,
        graph,
        penalty_model
    WHERE
        penalty_model.ising_model_id = ising_model.id
        AND feasible_configurations.id = penalty_model.feasible_configurations_id
        AND graph.id = ising_model.graph_id;
    """
