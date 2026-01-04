# Marta do Tibino - AI Assistant

Este projeto é uma assistente de IA, chamada Marta, projetada para gerir reservas para o restaurante Tibino na Foz do Arelho.

## Estrutura do Projeto

O **backend da Marta** está alojado num repositório GitHub, chamado `tibino-backend`.
O **frontend** (site do menu/carta de vinhos) é uma aplicação separada, alojada no Netlify.

A estrutura de módulos do backend (`tibino-backend`) é a seguinte, cada um com uma responsabilidade específica:

- **`app.py`**: O ficheiro principal da aplicação FastAPI, que inicializa a aplicação e define as rotas da API.
- **`models.py`**: Contém todos os modelos de dados Pydantic usados para validação de requisições e respostas.
- **`config.py`**: Contém toda a configuração da aplicação, como horários de funcionamento do restaurante, capacidade e duração da sessão.
- **`responses.py`**: Armazena todas as respostas traduzidas que a Marta pode enviar ao utilizador.
- **`sessions.py`**: Gere as sessões do utilizador, incluindo criação, recuperação e limpeza de sessões expiradas.
- **`logic.py`**: Contém a lógica de negócio principal da assistente, incluindo processamento de mensagens e reconhecimento de intenção.
- **`pratos_do_dia.py`**: Armazena os pratos especiais do dia do restaurante.
- **`.env`**: Ficheiro de variáveis de ambiente.
- **`requirements.txt`**: Uma lista de todas as dependências do projeto.
- **`README.md`**: Este ficheiro, que contém a documentação do projeto.

## Módulos

### `app.py`

This is the entry point of the application. It contains:
- The FastAPI application instance.
- The API routes (`/chat` and `/`).

### `models.py`

This module defines the following Pydantic models:
- **`Reservation`**: Represents a reservation with `name`, `phone`, `reservation_time`, and `party_size`.
- **`SessionData`**: Holds session-specific data, such as `session_id`, `language`, and any associated `reservation`.
- **`UserInput`**: Defines the structure of the user's input, containing the `session_id` and the `text` of the message.
- **`ChatResponse`**: Defines the structure of the assistant's response, containing the `session_id` and the response `text`.

### `config.py`

This file centralizes the application's configuration:
- **`MAX_CAPACITY`**: The maximum number of people the restaurant can hold.
- **`OPENING_HOURS`**: A dictionary defining the restaurant's opening hours for lunch and dinner, including new rules for weekdays, weekends, and closing days (Tuesdays).
- **`LAST_RESERVATION_TIME_LUNCH`**: The latest time a lunch reservation can be made.
- **`LAST_RESERVATION_TIME_DINNER`**: The latest time a dinner reservation can be made.
- **`SESSION_TTL`**: The time-to-live for a user session.

### `responses.py`

This module contains the `RESPONSES` dictionary, which holds all the possible responses for Marta, translated into Portuguese, English, and French.

### `sessions.py`

This module is responsible for session management:
- **`get_session(session_id)`**: Retrieves an existing session or creates a new one.
- **`cleanup_expired_sessions()`**: Removes sessions that have expired based on `SESSION_TTL`.
- **`sessions`**: An in-memory dictionary to store active sessions.

### `menus.py`

This module contains the `MENUS` dictionary, which stores the daily menus. The keys are dates in `YYYY-MM-DD` format.

### `logic.py`

Este módulo contém a lógica central da assistente. Foi significativamente atualizado para gerir um novo fluxo de reserva em duas etapas, que inclui a confirmação por parte do staff.

- **`process_message(session, user_input)`**: Processa a mensagem do utilizador. Agora, além de interpretar a linguagem natural, verifica se existe uma reserva pendente de confirmação do staff. Se o input for uma confirmação do staff (ex: "ok mesa 7"), processa-a. Caso contrário, inicia ou continua o fluxo de reserva.
- **`parse_reservation_request(text)`**: Função principal que tenta extrair todos os detalhes necessários para a reserva (data, hora, nome, telefone, número de pessoas) a partir do texto.
- **`stage_reservation(session, details)`**: Esta função valida o pedido de reserva inicial (horário, capacidade, limites de hora). Se tudo estiver correto, armazena os detalhes da reserva como "pendente" na sessão do cliente, devolve uma mensagem de estágio ao cliente e prepara uma mensagem para o staff (simulada).
- **`confirm_reservation(session, table_number)`**: Confirma uma reserva que estava em estágio, atribuindo um número de mesa. Move a reserva de "pendente" para "confirmada" e devolve uma mensagem de confirmação final ao cliente, incluindo o menu do dia e o número da mesa.
- **`format_date_for_user(dt, lang)`**: Formata objetos `datetime` para uma string amigável ao utilizador (ex: "dia 3 de janeiro").

#### Parsing de Linguagem Natural
Um conjunto de funções auxiliares trabalha em conjunto para extrair informações da mensagem do utilizador, com melhorias na interpretação de horas por extenso (e.g., "catorze horas") e datas relativas (e.g., "amanhã"):
- **`parse_datetime_from_text(text)`**: Entende datas relativas como "hoje" e "amanhã", dias da semana, e horas por extenso ou com formato "HHhMM".
- **`extract_name(text)`**: Encontra nomes no texto.
- **`extract_phone(text)`**: Encontra números de telefone.
- **`extract_party_size(text)`**: Encontra o número de pessoas para a reserva, entendendo tanto dígitos ("2") como palavras ("dois").

#### Outras Funções
- **`is_open(dt)`**: Uma função auxiliar que verifica se o restaurante está aberto numa dada `datetime`, considerando os novos dias de fecho (terça-feira).
- **`get_total_people_at(dt)`**: Uma função auxiliar que calcula o número total de pessoas com reservas num determinado momento, para verificar a `MAX_CAPACITY`.
- **`reservations`**: Um dicionário em memória para armazenar as reservas **confirmadas**.

#### Simulação da Comunicação com Staff
A comunicação com o "grupo Staff no WhatsApp" e a espera de 5 minutos são **simuladas**. Após o cliente fazer um pedido de reserva, a Marta informará que irá confirmar com a equipa e mostrará o que seria enviado para o grupo de WhatsApp. A sua resposta (do utilizador) a seguir, como "ok mesa 7", será interpretada como a resposta do staff para prosseguir com a confirmação.

### `pratos_do_dia.py`

Este módulo contém o dicionário `PRATOS_DO_DIA`, que armazena os pratos especiais que mudam diariamente. As chaves são os nomes dos dias da semana (em inglês, minúsculas). Não contém o menu fixo nem a carta de vinhos.
Exemplo:
```python
PRATOS_DO_DIA = {
    "saturday": ['marisco', 'choco frito', 'arroz de tamboril'],
    "sunday": ['arroz de tamboril', 'bacalhau à brás'],
    "monday": ['salmão grelhado', 'arroz de tamboril'],
    "tuesday": [], # fechado
    "wednesday": ['enguias à caldeirada', 'cabrito assado'],
    "thursday": ['leitão à bairrada', 'rojões'],
    "friday": ['bacalhau à brás', 'choco frito']
}
```

## Exemplo de Simulação (Reserva com Confirmação do Staff)

Esta simulação demonstra o fluxo de reserva completo, incluindo a fase de confirmação pelo staff.

### **Passo 1: Cliente faz um pedido de Reserva**

**Cliente envia:** `Quero reserva para dois amanhã às 14h, Nuno, 911111111`

**Marta responde ao Cliente:**
```
Ok, vou confirmar com a equipa.
```

**Mensagem 'enviada' para o grupo Staff no WhatsApp (simulada):**
```
Reserva: dia 4 de janeiro 14:00, Nuno, 911111111, 2 pessoas – alguém confirma?
```

**Estado do dicionário `reservations` neste momento:**
```python
{}
```

### **Passo 2: Staff Confirma (simulado)**

**Staff envia (simuladamente):** `ok mesa 7`

**Marta responde ao Cliente:**
```
Feito! Mesa 7 dia 4 de janeiro às 14:00. Ah, e Menu do dia: Arroz de Tamboril, Bacalhau à Brás.
```

**Estado final do dicionário `reservations` (após confirmação):**
```python
{
  "algum-id-de-sessao-gerado-aleatoriamente": {
    "name": "Nuno",
    "phone": "911111111",
    "reservation_time": "2026-01-04T14:00:00",
    "party_size": 2
  }
}
```

---

## Exemplo de Simulação (Reserva Rejeitada para Terça-feira)

Esta simulação demonstra que a Marta rejeita corretamente pedidos de reserva para o dia de encerramento do restaurante.

### **Passo 1: Cliente faz um pedido de Reserva para Terça-feira**

**Cliente envia:** `Quero reserva para dois terça às 14h, João, 912222222`

**Marta responde ao Cliente:**
```
Estamos abertos de Quarta a Segunda. Almoço: 12h-15h. Jantar: 19h-23h (cozinha encerra às 22h). Encerramos à Terça-feira.
```

**Mensagem 'enviada' para o grupo Staff no WhatsApp (simulada):**
Nenhuma mensagem é enviada ao staff, pois a reserva é rejeitada logo na primeira validação.

**Estado do dicionário `reservations` (interno da Marta):**
```python
{}
```

---

## Exemplo de Simulação (Reserva para Segunda-feira com Confirmação do Staff)

Esta simulação demonstra o fluxo de reserva completo para um dia útil, incluindo a fase de confirmação pelo staff.

### **Passo 1: Cliente faz um pedido de Reserva**

**Cliente envia:** `Quero reserva para dois segunda às 14h, Maria, 913333333`

**Marta responde ao Cliente:**
```
Ok, vou confirmar com a equipa.
```

**Mensagem 'enviada' para o grupo Staff no WhatsApp (simulada):**
```
Reserva: dia 5 de janeiro 14:00, Maria, 913333333, 2 pessoas – alguém confirma?
```

**Estado do dicionário `reservations` neste momento:**
```python
{}
```

### **Passo 2: Staff Confirma (simulado)**

**Staff envia (simuladamente):** `ok mesa 5`

**Marta responde ao Cliente:**
```
Feito! Mesa 5 dia 5 de janeiro às 14:00. Ah, e Menu do dia: Salmão Grelhado, Arroz de Tamboril.
```

**Estado final do dicionário `reservations` (após confirmação):**
```python
{
  "algum-id-de-sessao-gerado-aleatoriamente-1": {
    "name": "Maria",
    "phone": "913333333",
    "reservation_time": "2026-01-05T14:00:00",
    "party_size": 2
  }
}
```

---

**Conclusão:** O fecho à terça-feira foi testado e está correto.

---

### **Marta - Funcionalidade de Menu Completo**

A Marta agora consegue responder a perguntas sobre o menu completo e a carta de vinhos, redirecionando o cliente para o site do restaurante.

## API Endpoints

### `POST /chat`

This is the main endpoint for interacting with Marta.
- **Request Body**: A `UserInput` object containing the `session_id` (optional) and the `text` of the user's message.
- **Response Body**: A `ChatResponse` object containing the `session_id` and the assistant's `text` response.

### `GET /`

A simple endpoint to check if the application is running.

## How to Run

1.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Run the application**:
    ```bash
    uvicorn app:app --reload
    ```
The application will be available at `http://127.0.0.1:8000`. You can access the API documentation at `http://127.0.0.1:8000/docs`.
