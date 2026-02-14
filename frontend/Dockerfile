# Usa un'immagine PHP con Apache
FROM php:7.4-apache

COPY 000-default.conf /etc/apache2/sites-available/000-default.conf   

# Imposta il documento root per Apache
WORKDIR /var/www/html

# Copia i file dell'applicazione nell'immagine Docker
COPY . /var/www/html

RUN chmod -R 755 assets
RUN chmod -R 755 js
RUN chmod -R 755 css
RUN rm js/config.json
RUN mv js/configProd.json js/config.json

# Abilita il modulo Apache Rewrite per URL rewriting
RUN a2enmod rewrite

# Esponi la porta 80 per il traffico HTTP
EXPOSE 80

# Comando di avvio per Apache
CMD ["apache2-foreground"]
