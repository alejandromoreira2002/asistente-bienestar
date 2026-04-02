module.exports = {
  apps: [
    {
      name: 'prod-asistente-energetico',
      namespace: 'asistente-energetico',
      script: 'App.py',
      cwd: '/home/asistente-energetico',

      // Recarga automática al cambiar archivos
      watch: true,
      ignore_watch: [
        "storage",       // tus datos persistentes
        "docs/*",          // documentación o archivos de referencia
        "db",            // base de datos Milvus
        "static",        // si tienes archivos estáticos
        "static/docs/*", // si tienes archivos estáticos
        "logs",          // si generas logs en carpeta
        "node_modules",  // evita bucles infinitos
        ".git",
        "__pycache__"
      ],

      // Intérprete de Python
      interpreter: "python3",
      // interpreter: "/usr/local/bin/python3.10",

      // Manejo de fallos y logs
      autorestart: true,
      max_restarts: 10,
      restart_delay: 3000,
      error_file: "logs/err.log",
      out_file: "logs/out.log",
      merge_logs: true
    }
  ]
};
