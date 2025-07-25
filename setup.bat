@echo off
echo 🚀 Configurando Sistema de Procesamiento de Facturas con IA
echo ============================================================

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no está instalado. Por favor instala Python 3.11 o superior.
    pause
    exit /b 1
)

echo ✅ Python encontrado

REM Crear entorno virtual
echo 📦 Creando entorno virtual...
python -m venv venv
if errorlevel 1 (
    echo ❌ Error creando entorno virtual
    pause
    exit /b 1
)

echo ✅ Entorno virtual creado

REM Activar entorno virtual
echo 🔄 Activando entorno virtual...
call venv\Scripts\activate.bat

REM Actualizar pip
echo 📈 Actualizando pip...
python -m pip install --upgrade pip

REM Instalar dependencias
echo 📚 Instalando dependencias...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Error instalando dependencias
    pause
    exit /b 1
)

echo ✅ Dependencias instaladas

REM Crear archivo .env si no existe
if not exist .env (
    echo 📝 Creando archivo .env...
    copy .env.example .env
    echo ⚠️  IMPORTANTE: Edita el archivo .env y configura tu OPENAI_API_KEY
)

REM Crear directorios necesarios
echo 📁 Creando directorios...
if not exist uploads mkdir uploads
if not exist logs mkdir logs

echo ✅ Configuración completada!
echo.
echo 📋 Próximos pasos:
echo    1. Edita el archivo .env y configura tu OPENAI_API_KEY
echo    2. Ejecuta: python run.py
echo    3. Abre http://localhost:8000/docs en tu navegador
echo.
echo 🧪 Para probar el sistema: python test_system.py ruta_a_tu_factura.pdf
echo.
pause
