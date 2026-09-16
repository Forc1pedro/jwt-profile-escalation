#  instalação:
 pip install requests
#
#  uso:
    # 1. cola seu Bearer token em TOKEN = 'SEU_TOKEN_AQUI'
    # 2. roda
   python profile_escalate.py
#
#  fluxo:
#
#  1. GET /api/me — lê a estrutura real do JSON de perfil
#  2. detecta automaticamente campos de role (role, cargo, perfil, nivel, etc.)
#  3. PUT /api/me com o perfil completo modificado
#  4. fallback automático para PATCH se o servidor rejeitar PUT
#  5. segundo GET confirma se a mudança foi aceita
#
#  nota: se o servidor retornar 200 mas o campo não mudar, o backend provavelmente tem validação server-side que ignora updates de role via self-service — nesse caso manda o response que aparece que a gente
#  acha outro vetor.
