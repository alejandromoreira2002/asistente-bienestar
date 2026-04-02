from modelos.agentes import AgentesModelo, State
#from controladores.embedding import EmbeddingManager
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig
from typing import Generator, List, Dict, Union
import os

class AgentesControlador:
    def __init__(self, app):
        self.modelo = AgentesModelo(app)
        self.graph_builder = StateGraph(State)
        self.memory = InMemorySaver()
    
    def crearHilo(self):
        idHilo = self.modelo.getIdHilo()
        return idHilo
    
    def construirGrafo(self):
        (
            consulta_usuario, 
            tools_node, 
            get_intencion, 
            generate, 
            nodo_consumo, 
            conector_consumo_prediccion, 
            nodo_prediccion,
            consulta_usuario2,
            deteccion_intencion
        ) = self.modelo.getNodos(END, START)
        
            
        self.graph_builder.add_node("deteccion_intencion", deteccion_intencion)
        self.graph_builder.add_node("consulta_usuario", consulta_usuario)
        self.graph_builder.add_node("consulta_usuario2", consulta_usuario2)

        self.graph_builder.add_edge(START, "deteccion_intencion")
        # self.graph_builder.add_edge("deteccion_intencion", END)
        # self.graph_builder.add_edge("consulta_usuario", "consulta_usuario2")
        # self.graph_builder.add_edge(START, "consulta_usuario")
        self.graph_builder.add_edge("consulta_usuario2", END)
        
        return self.graph_builder.compile(checkpointer=self.memory)
    
    def reiniciarGrafo(self, thread_id):
        self.graph_builder = StateGraph(State)
        self.memory.delete_thread(thread_id)
        
        return self.construirGrafo()
    
    def mostrarGrafo(self, graph):
        return graph.get_graph().draw_mermaid_png()
    
    def stream_tokens(
        self,
        hilo: str,
        tipo: str,
        mensajes: Union[str, List[Dict[str, str]]],
        cancel_event=None
    ) -> Generator[str, None, None]:
        print("Mensajes recibidos antes de la respuesta:")
        
        config: RunnableConfig = {"configurable": {"thread_id": "abc123"}}
        
        human_response = None
        while True:
            if not human_response:
                input_message = input("Escriba un mensaje...")
                human_response = {"messages": [{"role": "user", "content": input_message}]}
            #print(human_response)
        # meta = []
            for clas, chunk in self.graph_builder.stream(
                human_response,
                stream_mode=["values", "messages"] ,
                config=config,
            ):

                if clas == 'messages':
                    #print(chunk)
                    print(chunk[0].content, end='')
                    
                if clas == 'values' and '__interrupt__' in chunk:
                    #print(f"Interrupt:{chunk}")
                    msg = chunk['__interrupt__'][-1].value
                    human = input(f"[INTERRUPT '{msg}']: ")
            
                    human_response = Command(
                        resume = human
                    )
                    break
                
                human_response = None
        
        
        # Delegar streaming de tokens al modelo
        #yield from self.modelo.stream_llm(prompt_text, cancel_event=cancel_event)
    
    