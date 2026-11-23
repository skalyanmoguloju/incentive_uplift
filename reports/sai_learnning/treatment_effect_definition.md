# Treatment-Effect Definition

## 1. Notation 

This defines how the information processed is presented for understanding

For customer i:
- X_i represents the customer features.
- T_i represents the treatment received.
- T_i = 0 represents the control treatment, where the customer have not received any offer.
- T_i = t represents receipt of offer t.
- Y_i(t) represents the outcome that would be observed if customer i received treatment t (control or offer).

## 2. Outcomes

For each customer, there is a outcome for every treatment. For example, a customer may have one outcome if they receive no offer, another if they receive a specific offer, and another if they receive a different offer.

Only one of these outcomes is observed for each customer because each customer receives only one treatment in the setup. The outcomes under the other treatments are counterfactual outcomes.

## 3. Treatment Effect

Each modeling row represents one customer-treatment decision during a defined observation window. The customer receives only one actual treatment in that decision. The model estimates the outcomes under the other treatments as counterfactual predictions.

The treatment effect of offer t for customer i is defined as:

τ_i(t) = E[Y_i(t) | X_i] − E[Y_i(0) | X_i]

This represents the difference between the customer’s expected outcome after receiving offer t and the customer’s expected outcome without receiving an offer.

## 4. Multi-Treatment Uplift

Because the project contains multiple offers, the model will estimate an uplift value for each offer:

τ_i(1), τ_i(2), ..., τ_i(10)

A positive uplift value indicates that the offer is expected to increase the customer’s probability of conversion compared with the control condition.

A negative uplift value indicates that the customer may be less likely to convert with the offer than without an offer.

The best treatment for customer i can be selected using:

t_i* = argmax_t τ_i(t)

If all offer uplift values are negative, the model may recommend the control condition.

## 5. Observed Outcome

The observed outcome for customer i is determined by the treatment actually received:

Y_i = Y_i(T_i)

In this project, the outcome will represent whether the customer makes a qualifying purchase within the defined observation window.

The exact rule for connecting a transaction to an offer will be established during event reconstruction.

## 6. Modeling Assumption

The model estimates counterfactual outcomes from customer features, historical behavior, and offer information. Since only one treatment outcome is observed for each customer, the other treatment outcomes must be estimated.

The analysis assumes that the available customer features contain enough information to adjust for important differences between customers who receive different offers. However, because the dataset is observational and treatment assignment is not confirmed to be randomized, the estimated treatment effects should be interpreted as model-based uplift estimates rather than definitive causal effects.