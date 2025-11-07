from nicegui import ui, app
from dotenv import load_dotenv
import requests
import os

# Carregamento de Credenciais no.env
load_dotenv()
API_URL = os.getenv("API_URL")
USUARIO = os.getenv("LOG_USER")
SENHA = os.getenv("LOG_PASSWORD")

# css
BACKGROUND_STYLE = '''
<style>
body {
    background-image: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url('/image/asa.jpg');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}
</style>
'''
# Inicializa o estado da aplicação e os atributos da UI
class BoardingSystemUI:    
    def __init__(self):
        self.logged_in = False
        self.passenger_table = None
        self.passenger_select = None
        self.name_input = None
        self.flight_input = None
        self.origin_input = None
        self.destination_input = None
        self.seat_input = None

    
    # Constrói e exibe a página de login
    def show_login_page(self):        
        ui.add_head_html(BACKGROUND_STYLE)

        if self.logged_in:
            ui.navigate.to('/dashboard')
            return

        with ui.card().classes("absolute-center w-96 bg-opacity-90"):
            ui.label("🔐 Login").classes("text-2xl font-bold self-center")
            self.user_input = ui.input("Usuário").props('outlined')
            self.password_input = ui.input("Senha", password=True, password_toggle_button=True).props('outlined')
            ui.button("Entrar", on_click=self.handle_login).classes("w-full")

    # Constrói e exibe a página principal (dashboard)
    def show_dashboard_page(self):        
        ui.add_head_html(BACKGROUND_STYLE)

        if not self.logged_in:
            ui.notify('Acesso negado. Por favor, faça o login.', color='negative')
            ui.navigate.to('/')
            return

        self._build_header()
        self._build_metrics()
        self._build_registration_form()
        self._build_passenger_list()
        
        self.update_passenger_list()

   
    def handle_login(self):
        if self.user_input.value == USUARIO and self.password_input.value == SENHA:
            self.logged_in = True
            ui.notify("Login realizado com sucesso ✅", type="positive")
            ui.navigate.to("/dashboard")
        else:
            ui.notify("Utilizador ou senha incorretos ❌", type="negative")

    def handle_logout(self):
        self.logged_in = False
        ui.notify('Sessão terminada com sucesso.', color='info')
        ui.navigate.to('/')

    def handle_register_passenger(self):
        form_data = {
            "NAME": self.name_input.value,
            "FLIGHT": self.flight_input.value,
            "ORIGIN": self.origin_input.value,
            "DESTINATION": self.destination_input.value,
            "SEAT": self.seat_input.value
        }

        if not all(form_data.values()):
            ui.notify("Por favor, preencha todos os campos ⚠️", type="warning")
            return

        try:
            response = requests.post(API_URL, json=form_data)
            if response.status_code == 200:
                ui.notify("Passageiro registado com sucesso ✅", type="positive")
                self.update_passenger_list()
                for field in [self.name_input, self.flight_input, self.origin_input, self.destination_input, self.seat_input]:
                    field.value = ""
            else:
                error_message = response.json().get('detail', 'Erro ao registar passageiro ❌')
                ui.notify(error_message, type="negative")
        except requests.RequestException as e:
            ui.notify(f"Erro de ligação com a API: {e}", type="negative")

    def handle_checkin(self):
        passenger_id = self.passenger_select.value
        if not passenger_id:
            ui.notify("Por favor, selecione um passageiro ⚠️", type="warning")
            return

        try:
            response = requests.post(f"{API_URL}/{passenger_id}/checkin")
            if response.status_code == 200:
                ui.notify("Check-in realizado com sucesso ✅", type="positive")
                self.update_passenger_list()
            else:
                ui.notify("Erro ao realizar o check-in ❌", type="negative")
        except requests.RequestException as e:
            ui.notify(f"Erro de ligação com a API: {e}", type="negative")
    
    # Comunicação com a API 
    def get_passenger_data(self):
        try:
            response = requests.get(API_URL)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            ui.notify(f"Erro ao carregar passageiros: {e}", type="negative")
            return []

    def update_passenger_list(self):
        passengers = self.get_passenger_data()
        
        for p in passengers:
            p["CHECKIN_STATUS"] = "SIM ✅" if p["CHECKIN_STATUS"] == 1 else "NÃO ❌"
            
        self.passenger_table.rows = passengers
        self.passenger_select.options = [p["id"] for p in passengers]
        self.passenger_select.update()

    # Construção da UI 
    def _build_header(self):
        with ui.row().classes('w-full items-center justify-between'):
            ui.label("🛫 Sistema de Embarque").classes("text-3xl font-bold text-white")
            ui.button("Sair", on_click=self.handle_logout, icon='logout', color='negative')

    def _build_metrics(self):
        with ui.row().classes("gap-8 my-6 w-full justify-center"):
            passengers = self.get_passenger_data()
            total = len(passengers)
            checkins = sum(1 for p in passengers if p.get('CHECKIN_STATUS') == 1)
            with ui.card().classes('bg-white bg-opacity-25'):
                 ui.label(f"👥 Passageiros Registados: {total}").classes("text-lg")
                 ui.label(f"🛂 Check-ins Realizados: {checkins}").classes("text-lg")

    def _build_registration_form(self):
        with ui.card().classes("w-full max-w-lg mx-auto bg-opacity-90"):
            ui.label("📋 Registar Novo Passageiro").classes("text-xl font-bold")
            self.name_input = ui.input("Nome")
            self.flight_input = ui.input("Voo")
            self.origin_input = ui.input("Origem")
            self.destination_input = ui.input("Destino")
            self.seat_input = ui.input("Assento")
            ui.button("Registar", on_click=self.handle_register_passenger).classes("mt-2 w-full")

    def _build_passenger_list(self):
        with ui.card().classes('w-full mt-6 bg-opacity-90'):
            ui.label("📑 Passageiros Registados").classes("text-xl font-bold")
            columns = [
                {"name": "id", "label": "ID", "field": "id", "sortable": True},
                {"name": "NAME", "label": "Nome", "field": "NAME", "sortable": True},
                {"name": "FLIGHT", "label": "Voo", "field": "FLIGHT"},
                {"name": "ORIGIN", "label": "Origem", "field": "ORIGIN"},
                {"name": "DESTINATION", "label": "Destino", "field": "DESTINATION"},
                {"name": "SEAT", "label": "Assento", "field": "SEAT"},
                {"name": "CHECKIN_STATUS", "label": "Check-in", "field": "CHECKIN_STATUS", "sortable": True},
            ]
            self.passenger_table = ui.table(columns=columns, rows=[], row_key="id").classes("w-full")

            with ui.row().classes('mt-4 w-full items-center justify-center gap-4'):
                self.passenger_select = ui.select([], label="Selecione o ID para Check-in").classes('w-64')
                ui.button("Realizar Check-in", on_click=self.handle_checkin)

# Ponto de Entrada da Aplicação 
boarding_ui = BoardingSystemUI()
app.add_static_files('/image', 'image')

ui.page("/")(boarding_ui.show_login_page)
ui.page("/dashboard")(boarding_ui.show_dashboard_page)

ui.run(port=8080, reload=True)
