# <System or design question>

## Goal and constraints

- **Reader:** <Who needs this design>
- **Goal:** <What the system must do>
- **Constraints:** <Scale, latency, availability, cost, or scope that affects the design>

## Context

<Name the users and external systems. State what is in and out of scope.>

![System context and external dependencies.](diagrams/context.svg)

Figure 1. System context and external dependencies. See the [D2 source](diagrams/context.d2).

## Main components

<Explain the responsibilities that satisfy the goal. Add a container or component view only when it answers a concrete question.>

## Primary flow

![Primary request and response flow.](diagrams/request-flow.svg)

Figure 2. Primary request and response flow. See the [D2 source](diagrams/request-flow.d2).

## Trade-offs and failure behavior

- <State one decision and the requirement it serves.>
- <State a relevant failure path and how the system responds.>

## Open questions

- <List only unresolved decisions that affect the design.>
