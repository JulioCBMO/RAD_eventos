# Inscrições em Eventos do Campus — RAD / IFPB

## Integrantes
- Julio Cesar Batista de Medeiros Oliveira

## Contas de teste (senha de todas: `senha123`)
| Usuário | Papel | Uso |
|---|---|---|
| admin | Superusuário | Cadastrar salas no Admin |
| organizador2 | Organizador (grupo Organizadores) | Dono da Semana Acadêmica |
| organizador3 | Organizador (grupo Organizadores) | Dono da Jornada Científica; testar que não altera o que é do 2 |
| participante4 | Participante | Inscrever-se |
| participante5 | Participante | Ocupar a última vaga da sala de 2 lugares |

## Dados cadastrados
**Salas:** Auditório (100), Laboratório 1 (30), **Sala Pequena (capacidade 2)**.

**Eventos (períodos que se cruzam em 11–12/nov/2026):**
- Semana Acadêmica — 10/11 a 12/11 (organizador2)
- Jornada Científica — 11/11 a 13/11 (organizador3)

**Atividades:**
| Atividade | Evento | Sala | Horário |
|---|---|---|---|
| Palestra de abertura | Semana | Auditório | 11/11 09–10h |
| Mesa-redonda | Semana | Sala Pequena | 11/11 09–10h |
| Palestra sobre Django | Semana | Auditório | 11/11 14–16h |
| Oficina de UX | Semana | Sala Pequena (cap. 2) | 12/11 09–11h |
| Treinamento de Git | Jornada | Laboratório 1 | 11/11 09–11h |
| Apresentação de pôsteres | Jornada | Auditório | 12/11 14–17h |

- **Mesmo horário, salas distintas:** Palestra de abertura, Mesa-redonda (mesmo evento, critério 18) e Treinamento de Git (outro evento, critério 19).
- **Mesma sala, horários que não se cruzam:** Auditório (abertura 9–10h, Django 14–16h, pôsteres no dia 12).
- **Sala de capacidade 2:** Oficina de UX (Sala Pequena).

## Como rodar
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py runserver
```

## Requisitos não feitos
Desafio opcional (lista de espera): não feito.