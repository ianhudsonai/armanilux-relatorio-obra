# Dias úteis

A conta é só a de `scripts/business_days.py`. Não refazer de cabeça e não trocar a cidade.

Contagem: dias úteis depois da data inicial, até a data final inclusive. O próprio dia inicial não entra. O mesmo dia vale 0.

Não entram:

- sábado e domingo
- feriados nacionais brasileiros (calendário `holidays`, país BR)
- segunda-feira e terça-feira de Carnaval
- 9 de julho, feriado do estado de São Paulo
- 25 de janeiro e Corpus Christi, feriados da cidade de São Paulo

A quarta-feira de Cinzas continua dia útil. O relatório deve dizer essa convenção.

Leitura, usada na cor da tabela e das barras:

- até 2 dias úteis: fluxo contínuo
- de 3 a 5: atenção
- 6 ou mais: intervalo longo

Intervalo longo não é, por si só, atraso da Armanilux. Se o grupo não explica aqueles dias, a causa é `dado não identificado`.
