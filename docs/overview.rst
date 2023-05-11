Overview & Usage
=======================================


Example Task
--------------------------------
The LickWithhold task is an example of a head fixing task that AutoHeadFix can control, and is described as follows.

Upon initializing, AutoHeadFix will wait for a mouse to enter the headfixing area, with a prompt :code:`Waiting for a mouse...` For testing, we can use a spare RFID tag to simulate mouse entry.

After the ID is detected, AutoHeadFix will wait on the ContactCheck, which in this case is a BeamBreak  (:code:`AHF_ContactCheck_BeamBreak`). For testing, simply break the beam manually.

Upon beam break, the camera and brainlight will turn on and the trial will commence. The trial will be selected based on the mouse level, as described in :ref:`stimulator`. The stimulus is provided by :code:`AHF_Stimulus_VibMotor`, and the program determines trial requirements through the :code:`AHF_LickDetector_MPR`. 


Code Structure
--------------------------------
Everything is called from :code:`__main__2.py`, which initializes an :code:`AHF_Task`.

:code:`AHF_Task` contains a reference to one instance of each class:

| :code:`AHF_HeadFixer`
| :code:`AHF_Stimulus`
| :code:`AHF_Stimulator`
| :code:`AHF_Rewarder`
| :code:`AHF_Reader`
| :code:`AHF_Camera`
| :code:`AHF_ContactCheck`
| :code:`AHF_BrainLight`
| :code:`AHF_Trigger`
| :code:`AHF_LickDetector`
| :code:`AHF_DataLogger`
| :code:`AHF_Notifier`
| :code:`AHF_Subjects`

The roles and definitions of each class can be found at :ref:`modules`.

Each module is implemented by a specific subclass, depending on the task configuration \(see :ref:`below<task-config>`\). Existent task descriptions can be found at :ref:`stimulator`.

There are often one or more subclasses available for each module, named :code:`AHF_[class]_[subclass]`. For example, :code:`AHF_Stimulator` has subclasses
:code:`AHF_Stimulator_LEDs`, :code:`AHF_Stimulator_Lever`, :code:`AHF_Stimulator_LickWithhold`, :code:`AHF_Stimulator_Rewards`.
For the LickWithhold task, :code:`AHF_Stimulator` is implemented by :code:`AHF_Stimulator_LickWithhold`, :code:`AHF_Camera` is implemented by :code:`AHF_Camera_PiCam`.


For every task, :code:`__main__2.py` performs the same loop. First, the database is
initialized; however, as of right now, the database is not working. Next the task is 
initialized from :code:`AHF_Task`. The main loop is then started, where the `TagReader` waits for
a mouse, fixes the mouse with the `HeadFixer`, then initiates the `Stimulator`` to handle task-spefic logic.

On keyboard interrupt, the program enters the AutoHeadFix Manager menu.
