import sqlite3
import os

def verificar_escala():
    db_path = '/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring/db.sqlite3'
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verificar escalas disponíveis
        cursor.execute("SELECT id, data, etapa, status FROM escalas_escala ORDER BY data DESC LIMIT 5")
        escalas = cursor.fetchall()
        
        print("=== ESCALAS DISPONÍVEIS ===")
        for escala in escalas:
            print(f"ID: {escala[0]}, Data: {escala[1]}, Etapa: {escala[2]}, Status: {escala[3]}")
        
        # Verificar especificamente 07/10/2025
        cursor.execute("SELECT id, data, etapa, status FROM escalas_escala WHERE data = '2025-10-07'")
        escala_target = cursor.fetchone()
        
        if escala_target:
            print(f"\n=== ESCALA 07/10/2025 ===")
            print(f"ID: {escala_target[0]}, Etapa: {escala_target[2]}, Status: {escala_target[3]}")
            
            # Verificar alocações
            cursor.execute("SELECT COUNT(*) FROM escalas_alocacaovan WHERE escala_id = ?", (escala_target[0],))
            total_alocacoes = cursor.fetchone()[0]
            
            # Verificar alocações sem grupo
            cursor.execute("""
                SELECT COUNT(*) 
                FROM escalas_alocacaovan av 
                LEFT JOIN escalas_servicogrupo sg ON av.id = sg.alocacao_id 
                WHERE av.escala_id = ? AND sg.id IS NULL
            """, (escala_target[0],))
            alocacoes_sem_grupo = cursor.fetchone()[0]
            
            print(f"Total alocações: {total_alocacoes}")
            print(f"Alocações sem grupo: {alocacoes_sem_grupo}")
            
            # Verificar algumas alocações
            cursor.execute("""
                SELECT av.id, s.cliente, s.servico, s.horario
                FROM escalas_alocacaovan av
                JOIN core_servico s ON av.servico_id = s.id
                LEFT JOIN escalas_servicogrupo sg ON av.id = sg.alocacao_id
                WHERE av.escala_id = ? AND sg.id IS NULL
                LIMIT 5
            """, (escala_target[0],))
            
            alocacoes_sample = cursor.fetchall()
            if alocacoes_sample:
                print("\nAmostras de alocações sem grupo:")
                for aloc in alocacoes_sample:
                    print(f"  - ID: {aloc[0]} | {aloc[1]} | {aloc[2]} | {aloc[3]}")
            
        else:
            print("\n❌ Escala 07/10/2025 não encontrada!")
            
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    verificar_escala()