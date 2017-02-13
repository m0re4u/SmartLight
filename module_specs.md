## Module Specification

Any module should either be a single `.py` file with at least
a function called `light_on`, or it should be a directory
with an `__init__` file behaving the same way.

#### light_on

The function `light_on` should behave as follows: it takes only 
a single default argument, namely `yml_path="../config.yml"`, 
and any other desired arguments should be put into config.yml.

The return value should be a 3-tuple with boolean values, 
representing the color that the lights linked to the module 
should take, with the values representing Red, Green and Blue
respectively, being either on or off. Other intensity values 
are not possible.