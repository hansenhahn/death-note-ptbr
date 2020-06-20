@echo off

echo "Caderninho's Assembler by DiegoHH"

rem Executa os packers de overlay, imagem e texto
cd Programas
call pack_images.bat
call pack_texts.bat
cd ..

rem Copia os arquivos de fonte
copy "Fontes\font.NFTR" "ROM Modificada\DEATHNOTEDS\data\data\font" /B/Y

rem Monta a ROM nova e gera um patch
cd ROM Modificada
call pack_rom.bat
call do_patch.bat
cd ..