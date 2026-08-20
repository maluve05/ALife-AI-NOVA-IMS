# Mathematical Model & Evolutionary Formulation

This document formalizes the mathematical models, probability distributions, neural network formulations, and evolutionary dynamics implemented in the **ALife Simulation Engine**.

---

## 1. Spatial Perception & Vision Model

### 1.1 Egocentric Coordinate Transformation
Each Prey agent has an orientation angle $\theta \in \{0, 1, 2, 3\}$, corresponding to:
* $0 = \text{North}\ (0^\circ)$
* $1 = \text{East}\ (90^\circ)$
* $2 = \text{South}\ (180^\circ)$
* $3 = \text{West}\ (270^\circ)$

Given relative egocentric offset $(\Delta x_r, \Delta y_r)$, the absolute world coordinate $(x_a, y_a)$ is determined by the transformation matrix:

$$\begin{pmatrix} x_a \\ y_a \end{pmatrix} = \begin{pmatrix} x \\ y \end{pmatrix} + \mathbf{R}(\theta) \begin{pmatrix} \Delta x_r \\ \Delta y_r \end{pmatrix}$$

Where:
$$\mathbf{R}(0) = \begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}, \quad \mathbf{R}(1) = \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}, \quad \mathbf{R}(2) = \begin{pmatrix} -1 & 0 \\ 0 & 1 \end{pmatrix}, \quad \mathbf{R}(3) = \begin{pmatrix} 0 & -1 \\ -1 & 0 \end{pmatrix}$$

### 1.2 Concentric Vision Rings
Vision is organized into 4 concentric Manhattan/Chebyshev perimeter rings of distance $r \in \{1, 2, 3, 4\}$:
* Ring 1: $8 \times 1 = 8$ cells
* Ring 2: $8 \times 2 = 16$ cells
* Ring 3: $8 \times 3 = 24$ cells
* Ring 4: $8 \times 4 = 32$ cells
* Total cells sampled: $\sum_{r=1}^4 8r = 80$ cells.

The vision radius $r_{\text{vis}} \in \{1, 2, 3, 4\}$ is governed by the agent's current intelligence trait $I$:

$$r_{\text{vis}} = \min\left(\lfloor N_{\text{cells}}^{0.25} \rfloor,\ \begin{cases} 1 & \text{if } I < 25 \\ 2 & \text{if } 25 \le I < 50 \\ 3 & \text{if } 50 \le I < 75 \\ 4 & \text{if } I \ge 75 \end{cases}\right)$$

Cells beyond $r_{\text{vis}}$ are set to $0.0$. Cells within $r_{\text{vis}}$ are normalized:
$$v_{i} = \frac{\text{grid}[y_a][x_a]}{4.0}, \quad v_i \in [0.0, 1.0]$$
Out-of-bounds cells return $1.0$.

### 1.3 Vision Vector Assembly ($N = 81$)
$$\mathbf{x} = [v_1, v_2, \dots, v_{80}, v_{\text{hunger}}]^T, \quad v_{\text{hunger}} = \min\left(1.0, \max\left(0.0, \frac{E}{100.0}\right)\right)$$

---

## 2. Artificial Neural Network Dynamics

### 2.1 Feedforward Architecture
* **Input Layer**: $\mathbf{x} \in \mathbb{R}^{81}$
* **Hidden Layer**: $\mathbf{h} \in \mathbb{R}^{8}$, with weights $\mathbf{W}_h \in \mathbb{R}^{8 \times 81}$ and biases $\mathbf{b}_h \in \mathbb{R}^8$
* **Output Layer**: $\mathbf{y} \in \mathbb{R}^6$, with weights $\mathbf{W}_o \in \mathbb{R}^{6 \times 8}$ and biases $\mathbf{b}_o \in \mathbb{R}^6$

### 2.2 Activation Functions

#### Hidden Layer Activation (Clamped Sigmoid):
$$h_j = \sigma(z_j) = \begin{cases} 1.0 & \text{if } z_j > 20.0 \\ 0.0 & \text{if } z_j < -20.0 \\ \frac{1}{1 + e^{-z_j}} & \text{otherwise} \end{cases}$$
Where $z_j = \sum_{i=1}^{81} W_{h, j, i} x_i + b_{h, j}$.

#### Output Layer Activation (Numerically Stable Softmax):
$$P(\text{action}_k) = \frac{\exp(u_k - \max_m u_m)}{\sum_{l=1}^6 \exp(u_l - \max_m u_m)}$$
Where $u_k = \sum_{j=1}^8 W_{o, k, j} h_j + b_{o, k}$.

---

## 3. Vitality, Aging & Survival Dynamics

### 3.1 Life Expectancy ($LE$)
$$LE = 0.03125 \cdot E_0 \cdot \left(1 + \frac{N_{\text{prey}}}{N_{\text{predator}} + 1}\right)$$
Where $E_0$ is the initial prey energy parameter.

### 3.2 Gaussian Energy & Reproduction Scaling
Physical vitality follows a bell-shaped Gaussian curve centered at the midpoint of life expectancy ($\mu = \frac{LE}{2}$):

$$G(\text{Age}) = \exp\left(-\frac{1}{2}\left(\frac{\text{Age} - \mu}{\sigma}\right)^2\right), \quad \sigma = \frac{LE}{4}$$

* **Maximum Energy Capacity**:
  $$E_{\max}(\text{Age}) = E_0 \cdot \max(0.50, G(\text{Age}))$$
* **Reproduction Probability**:
  $$P_{\text{reproduction}}(\text{Age}) = P_0 \cdot G(\text{Age})$$

### 3.3 Logarithmic Survival Probability
Survival probability decays logarithmically with age:

$$P_{\text{survival}}(\text{Age}) = \max\left(0,\ 1 - \lambda \cdot \ln(\text{Age} + 1)\right)$$

Where the decay rate constant $\lambda$ is:
$$\lambda = \begin{cases} \frac{0.70}{LE \cdot (\ln(LE) - 1)} & \text{if } LE > 1 \text{ and } \ln(LE) > 1 \\ 0.005 & \text{otherwise} \end{cases}$$

### 3.4 Trait Maturation Functions
Base traits grow logarithmically as the individual accumulates experience:
$$\text{Efficiency}(\text{Age}) = \min\left(100.0,\ \text{BaseEfficiency} + 15.0 \cdot \ln(\text{Age} + 1)\right)$$
$$\text{Intelligence}(\text{Age}) = \min\left(100.0,\ \text{BaseIntelligence} + 15.0 \cdot \ln(\text{Age} + 1)\right)$$

---

## 4. Metabolic Energy Budget & Movement Costs

### 4.1 Locomotion Cost
Energy consumed per tick is inversely proportional to biological efficiency:

$$\Delta E = 2.0 \cdot \left(\frac{\text{BaseCost}}{\max(1.0, \frac{\text{Efficiency}}{10.0})} \cdot \delta_{\text{move}} \cdot \kappa_{\text{running}}\right) + 2.0 \cdot \text{BaseCost}$$

Where:
* $\delta_{\text{move}} = 1$ if moving, $0$ if stationary.
* $\kappa_{\text{running}} = 1.5$ for multi-step sprints, $1.0$ for regular steps.
* $\text{BaseCost} = \text{GENERATIONAL\_DECAY}$.

### 4.2 Reproduction Energy Cost
Both parents expend energy upon successful fertilization:
$$\Delta E_{\text{mating}} = 6.0 \cdot \frac{\text{GENERATIONAL\_DECAY}}{\max(1.0, \frac{\text{Efficiency}}{10.0})}$$

---

## 5. Genetic Recombination & Mutation

### 5.1 Crossover Recombination Operators
Given Parent 1 ($\mathbf{C}_1$) and Parent 2 ($\mathbf{C}_2$) of chromosome length $L = 712$:

1. **Single-Point Crossover**:
   $$\mathbf{C}_{\text{child}}[0 \dots k] = \mathbf{C}_1[0 \dots k], \quad \mathbf{C}_{\text{child}}[k+1 \dots L-1] = \mathbf{C}_2[k+1 \dots L-1]$$
   Where $k \sim U(1, L-2)$.
2. **Reverse Single-Point Crossover**:
   $$\mathbf{C}_{\text{child}}[0 \dots k] = \mathbf{C}_2[0 \dots k], \quad \mathbf{C}_{\text{child}}[k+1 \dots L-1] = \mathbf{C}_1[k+1 \dots L-1]$$
3. **Block-Based Functional Layer Crossover**:
   Segments are recombined according to functional ANN layer boundaries:
   $$\text{Blocks} = [0, 324, 648, 656, 704, 712]$$
   Alternating blocks are inherited from Parent 1 and Parent 2 respectively.

### 5.2 Gaussian Mutation with Boundary Clamping
Each gene $i \in \{0, \dots, L-1\}$ mutates with probability $p_m$:

$$C_i' = C_i + \mathcal{N}(0, 0.1^2) \quad \text{if } r \sim U(0, 1) < p_m$$

Subject to strict biological boundary constraints:
$$\text{Clamp}(C_i') = \begin{cases} \max(-2.0, \min(2.0, C_i')) & \text{if } i < 710 \text{ (ANN Weights/Biases)} \\ \max(5.0, \min(100.0, C_i')) & \text{if } i \ge 710 \text{ (Base Traits)} \end{cases}$$

---

## 6. Fitness Evaluation Metric

$$\text{Fitness}(p) = w_{\text{age}} \cdot \text{Age} + w_{\text{food}} \cdot \text{FoodEaten} + w_{\text{offspring}} \cdot \text{Offspring} + w_{\text{eff}} \cdot \text{Efficiency}$$

**Default Weights**:
$$w_{\text{age}} = 1.0, \quad w_{\text{food}} = 1.5, \quad w_{\text{offspring}} = 5.0, \quad w_{\text{eff}} = 0.5$$
