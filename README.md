![](https://github.com/navikt/knada-decorators/workflows/Build%20and%20deploy%20Profile%20Watcher/badge.svg)
![](https://github.com/navikt/knada-decorators/workflows/Build%20and%20deploy%20Namespace%20Decorator/badge.svg)

Knada Decorators
===================

> DecoratorController is an API provided by Metacontroller, designed to facilitate adding new behavior to existing
> resources. You can define rules for which resources to watch, as well as filters on labels and annotations.

[Metacontroller.app](https://metacontroller.github.io/metacontroller/) brukes for å automatisere oppgaver som har vært litt for kompliserte for rene k8s-ressurser.

## Metacontroller

Metacontroller og underapplikasjoner blir installert via [knada-yaml](https://github.com/navikt/knada-yaml/). Og lever i et eget namespace som heter `metacontroller`.
