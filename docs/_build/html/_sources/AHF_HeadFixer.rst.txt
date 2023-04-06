AHF\_HeadFixer 
======================

The HeadFixer class controls the headfixing mechanism. HeadFixer is implemented for two types of hardware: pistons, in :code:`AHF_HeadFixer_Pistons`, and servos, in :code:`AHF_HeadFixer_PWM_PCA9685`. Note that servos require extra parameters for fixation position. Currently, :code:`AHF_HeadFixer_PWM_PCA9685` is used for all tasks requiring headfixation.

:code:`AHF_HeadFixer_NoFix` is functionally equivalent to :code:`AHF_HeadFixer` with :code:`defaultPropHeadFix` set to 0; however, :code:`AHF_HeadFixer_NoFix` reduces setup and setdown overhead and does not require calibrating parameters.

AHF\_HeadFixer.AHF\_HeadFixer module
------------------------------------

.. automodule:: AHF_HeadFixer
   :members:
   :undoc-members:
   :show-inheritance:


AHF\_HeadFixer.AHF\_HeadFixer\_NoFix module
-------------------------------------------

.. automodule:: AHF_HeadFixer_NoFix
   :members:
   :undoc-members:
   :show-inheritance:

AHF\_HeadFixer.AHF\_HeadFixer\_PWM module
-----------------------------------------

.. automodule:: AHF_HeadFixer_PWM
   :members:
   :undoc-members:
   :show-inheritance:

AHF\_HeadFixer.AHF\_HeadFixer\_PWM\_PCA9685 module
--------------------------------------------------

.. automodule:: AHF_HeadFixer_PWM_PCA9685
   :members:
   :undoc-members:
   :show-inheritance:

AHF\_HeadFixer.AHF\_HeadFixer\_PWM\_Pi module
---------------------------------------------

.. automodule:: AHF_HeadFixer_PWM_Pi
   :members:
   :undoc-members:
   :show-inheritance:

AHF\_HeadFixer.AHF\_HeadFixer\_Pistons module
---------------------------------------------

.. automodule:: AHF_HeadFixer_Pistons
   :members:
   :undoc-members:
   :show-inheritance:

