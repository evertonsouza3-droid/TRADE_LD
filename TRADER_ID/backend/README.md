# Backend API

Esta API permite:

- cadastrar operações;
- listar operações salvas;
- executar uma simulação financeira simples.

## Como rodar

1. Abra o terminal na pasta do projeto.
2. Entre na pasta do backend:

   ```bash
   cd backend
   ```

3. Inicie o servidor com:

   ```bash
   python app/main.py
   ```

4. Depois abra no navegador:

   ```text
   http://127.0.0.1:8000
   ```

5. Se quiser verificar o status da API, acesse:

   ```text
   http://127.0.0.1:8000/
   ```

## Endpoints

### GET /

Retorna uma mensagem informando que a API está funcionando.

### POST /operations

Cria uma nova operação.

Exemplo de corpo JSON:

```json
{
  "name": "Compra",
  "symbol": "PETR4",
  "quantity": 10,
  "price": 35.5
}
```

Resposta esperada:

```json
{
  "id": 1,
  "name": "Compra",
  "symbol": "PETR4",
  "quantity": 10,
  "price": 35.5
}
```

### GET /operations

Lista todas as operações cadastradas.

### POST /simulation

Executa a simulação com os parâmetros informados.

Exemplo de corpo JSON:

```json
{
  "initial_value": 1000,
  "monthly_contribution": 200,
  "years": 5,
  "volatility": 0.15
}
```

Resposta esperada:

```json
{
  "projected_value": 15183.63,
  "annualized_return": 0.72296
}
```

## Como testar

Com o servidor rodando, execute:

```bash
python test_api.py
```

Esse script faz chamadas reais para a API e imprime os resultados no terminal.
