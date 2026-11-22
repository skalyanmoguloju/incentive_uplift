# Multi-Tower Uplift Model Architecture

## 1. Project Objective
- The project builds a model to predicts how the customer's behavior changes because of receiving an incentive.
- The model will estimates the incremental effect of each offer instead of just knowing whether the customer may purchase.
- The model will identifies customers who are likely to respond to purchase with an incentive.
- The model will supports selecting the best offer for each customer.
- The final goal is to improve conversions while considering incentive cost, profit, and return of investment.
- The model will be compared with logistic regression, LightGBM, and T-Learner baselines.

## 2. Treatment and Control

The treatment group contain customers who receive an offer or incenitve. The Starbucks dataset contains ten offer treatments: four BOGO offers, four discount offers, and two informational offers. Each offer is identified using its unique `offer_id`.

The control group contain customers presented with no offer during the observation window. This group represents the estimated customer behavior without an incentive.

The model outcome measures whether the customer completes the purchase after receiving the offer. The conversion is identified using qualified transaction events. The exact time window for connecting an offer with a customer outcome will be finalized during event reconstruction.

The model will compare the predicted outcome under each treatment with the predicted outcome under control settings. The difference represents the estimated incremental effect, or uplift, of the offer.

## 3. Input Features

The model will use customer, historical behavior, and offer-related that are available before the outcome is observed.

Customer features include age, income, gender, and membership duration (derived). Historical-behavior features include previous transaction count, previous spending, previous offers received, and previous offers viewed.

Offer features include offer type, reward, difficulty, duration, available communication channels, and the treatment or offer identifier.

Post-treatment information, such as future transactions, offer completion, future offer views, and future spending, will not be used as input features because these variables could cause data leakage.

## 4. Shared Representation

The model will initially process the customer and historical-behavior features using a shared representation network. Numerical features will be normalized before entering the network. Categorical features will be encoded appropriately.

The processed features will be combined and passed through fully connected neural-network layers. These shared layers will learn general patterns in customer behavior that are common across different treatments.

The output of the shared network will be a common customer representation. This representation will then be passed to treatment-specific towers, which will estimate the expected outcome under different offers.

Customer and history features
            ↓
Shared neural layers
            ↓
Common customer representation
            ↓
Treatment-specific towers


## 5. Treatment-Specific Towers

After populating the customer representation, the model will use separate treatment-specific towers to estimate the expected outcome under different conditions.

The model will include one tower for each of the ten offers and an additional control tower for the no-offer condition. Each tower will receive the customer representation and, when applicable, the features of its associated offer.

The towers will use separate neural-network layers so that each one can learn how different customer characteristics interact with a particular offer. The control tower will estimate the customer’s expected outcome without receiving an offer.

The outputs from all towers will be used to estimate the customer’s expected response under each available treatment.

## 6. Model Outputs

Each treatment-specific tower will produce a predicted probability that the customer will achieve the desired outcome under that treatment.

For each customer, the model will generate one predicted outcome for the control condition and one predicted outcome for each of the ten offers. Therefore, the model will produce eleven treatment-specific predictions.

These predictions will represent the expected probability of conversion if the customer receives a particular offer or receives no offer. The predictions will later be used to calculate uplift and select the most treatment for each customer.

## 7. Uplift Calculation

Uplift will be calculated by comparing the predicted outcome under each offer with the predicted outcome under the control.

For treatment t, the uplift score will be calculated as:

uplift(t) = predicted outcome under treatment t − predicted outcome under control

A positive uplift score indicates that the offer is expected to increase the customer’s probability of conversion compared with providing no offer. A negative uplift score indicates that the offer may perform worse than the control condition.

For each customer, the model can select the offer with the highest positive uplift. If all offer uplift scores are negative, the model may recommend the control condition.

## 8. Training Loss

The model can use binary cross-entropy loss to train the conversion predictions.

For each customer, the loss will be calculated using the prediction from the treatment that the customer actually received and the observed outcome for that customer. Predictions from the other treatment towers will not be directly compared with an outcome that was not observed for that customer.

The total training loss will be calculated as the average factual prediction loss across the training examples. The model parameters in the shared representation and treatment-specific towers will be updated through backpropagation.

## 9. Initial Architecture Sketch

flowchart TD
    A[Customer and historical features] --> B[Feature preprocessing]
    B --> C[Shared representation network]
    C --> D[Control tower]
    C --> E[Ten offer-specific towers]
    D --> F[Control conversion probability]
    E --> G[Offer conversion probabilities]
    F --> H[Uplift calculation]
    G --> H
    H --> I[Best offer or control recommendation]

## 10. Open Design Questions
The following design decisions will be finalized during data preparation and experimentation:

1. What time window should be used to connect an offer with a customer outcome?
2. How should customers with missing gender or income values be handled?
3. How should the treatment and control groups be balanced?
4. Should the model use one tower for every individual offer or group similar offers by offer type?
5. How should offer features be represented inside the treatment-specific towers?
6. How should treatment propensity scores be estimated?
7. What incentive costs should be used when calculating profit and return on investment?
8. How should the model handle customers who receive multiple offers?
9. What threshold should determine whether an offer is recommended over the control condition?
