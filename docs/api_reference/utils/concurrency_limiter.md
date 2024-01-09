---
title: Concurrency Limiters
description: Concurrency Limiters API reference
---

# Concurrency Limiters

This module contains the default concurrency limiter implementation in `arc` along with several helper functions to create common variants of it.

!!! note
    Concurrency limiters are **not** regular hooks and need a special decorator to be set. You can only have 1 concurrency limiter per command.

::: arc.utils.concurrency_limiter
