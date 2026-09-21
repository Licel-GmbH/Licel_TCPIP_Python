==============================
**SilentState Example**
==============================

The **SilentState** (``SILENCESTAT``) feature instructs the Ethernet controller
to *delay* the ``STAT?`` command sent to the selected transient recorder for a
configurable time window around every laser trigger. Only the ``STAT?`` status
query is held back during this window; all other commands are forwarded to the
recorder instantaneously, without any delay. Delaying the periodic ``STAT?``
polling suppresses the electrical noise that this traffic would otherwise inject
into the acquisition during the most sensitive part of the shot.

The silence window is defined by two delays, both expressed in microseconds:

- **pre-trigger block delay** : how long *before* the trigger the controller
  starts delaying the ``STAT?`` command.
- **post-trigger block delay** : how long *after* the trigger the controller
  keeps delaying the ``STAT?`` command before forwarding it again.

.. note::

   This feature is only available on newer controllers. Support is detected at
   runtime, the API issues a ``SILENCESTAT?`` query and, if the controller replies with
   ``unknown command``, the feature is considered unsupported and the API raises
   a ``RuntimeError`` (*"Ethernet controller does not support the SilentMode
   feature"*). Controllers that support the feature do not return
   ``unknown command``. See :class:`Licel.licel_SilentStat.SilentStat`.

Timing diagram
==============================

The diagram below shows the *silence window* the controller applies for a single
trigger. The ``STAT?`` command is delayed from ``preTriggerDelay`` microseconds
**before** the trigger edge until ``postTriggerDelay`` microseconds **after** it.
Outside this window the ``STAT?`` command is forwarded normally, and all other
commands are always forwarded instantaneously regardless of the window.

.. code-block:: text

    Controller -> Transient recorder  STAT? command

      forwarded                                              forwarded
    =================+                                             +=========>  t
                     |          STAT? DELAYED (silent)            |
                     |<---- preTrigDelay --->|<-- postTrigDelay -->|
                     |          (us)         ^      (us)           |
                     |                       |                     |
              delay starts             TRIGGER (t0)           delay ends
             (t0 - preTrigDelay)                          (t0 + postTrigDelay)

    Only the STAT? command is delayed within the window -- both before AND
    after the trigger. Other commands pass through without delay.
    Total silence window  =  preTrigDelay + postTrigDelay   [us]

For a periodic trigger the same window repeats once per shot:

.. code-block:: text

            silence window                 silence window
           |<------------->|              |<------------->|
    _______                 ______________                 _______   STAT? forwarded
           |               |              |               |
           |_______________|              |_______________|          STAT? delayed
                   ^                              ^
               trigger N                      trigger N+1
    (each silence window = preTrigDelay + postTrigDelay us; the trigger sits
     preTrigDelay into the window and postTrigDelay before its end)


SilentState Runtime Example
=================================================
.. toctree::
    :maxdepth: 1


    SilentState_Runtime_src


SilentState Store Example
===============================================
.. toctree::
    :maxdepth: 1
    
    SilentState_Store_src
