.. _accuracy_efficiency:

=================================
The accuracy/efficiency trade-off
=================================

Red AI vs Green AI
------------------

In the recent years we've seen great improvements in AI's performance especially in NLP tasks. 
While those were great breakthroughs, there were often achieved using excessive amount of data and 
computing power thus emiting a lot of CO2.
As Schwartz et al. [#]_ pointed out, nowadays, most of the AI and machine learning research is focused on 
improving models accuracy.
Not only does this paradigm leads to a race to computing power but 
it also exludes small contributors to take part in the community because of the cost necessary. 

Schwartz et al. advocates for a shift from, what they call, Red AI towards Green AI. 
This especially means a shift in reviews methodology to consider papers improving algorithms efficiency.

With this package, researchers can now monitor their energy consumption and we encourage them to report it in their publication.

Accurracy - efficiency trade-off
--------------------------------

Moving towards a greener AI means using more efficient algorithms.
In order to be more efficient, those algorithms allow to have smaller accuracy.

We find that in many use cases great efficiency improvements can be achieved 
at the small cost of losing a few percent in accuracy.

From our experience and as pointed by Patterson et al. [#]_, the following methods greatly compromise accuracy and efficiency:

* Model distillation, a method that transfers the knowledge from large models into smaller, 
  more computationally efficient models. 
  More details and an example: `huggingface - DistilBERT <https://medium.com/huggingface/distilbert-8cf3380435b5>`_
* Quantization is the action of using a less precise weights storage encoding. 
  `I-BERT <https://huggingface.co/kssteven/ibert-roberta-large>`_ stores ROBERTA's weights as ``int8`` allowing 4x inference speed up. 
  Quantization is now available on pytorch, see `pytorch quantization <https://pytorch.org/docs/stable/quantization.html#introduction-to-quantization>`_
* Pruning. In a neural network, some part of the network are totally unused because of weights close to 0.
  Pruning a network consists in removing those weights thus reducing the computing necessary to get a result.
  Pytorch offers an API to prune your network: `pytorch pruning <https://pytorch.org/tutorials/intermediate/pruning_tutorial.html>`_


----------

.. [#] Schwartz, R., Dodge, J., Smith, N. A., & Etzioni, O. (2019). Green ai. arXiv preprint
    `arXiv:1907.10597 <https://arxiv.org/pdf/1907.10597.pdf>`_
.. [#] Patterson, D., Gonzalez, J., Le, Q., Liang, C., Munguia, L. M., Rothchild, D., ... & Dean, J. (2021). 
    Carbon Emissions and Large Neural Network Training. arXiv preprint `arXiv:2104.10350 <https://arxiv.org/pdf/2104.10350.pdf>`_
