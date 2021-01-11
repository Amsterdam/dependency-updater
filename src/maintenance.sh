DATE=$(date +"%y-%m-%d")
BRANCH=feature/maintenance-$DATE
echo "$BRANCH"

declare -A array
array[bed-and-breakfast]=git@git.data.amsterdam.nl:Datapunt/bed-and-breakfast.git
array[iiif-metadata-server]=git@github.com:Amsterdam/iiif-metadata-server.git
array[iiif-auth-proxy]=git@github.com:Amsterdam/iiif-auth-proxy.git
array[waarnemingen-voertuigen]=git@github.com:Amsterdam/waarnemingen-voertuigen.git
array[waarnemingen-dashboard]=git@github.com:Amsterdam/waarnemingen-dashboard.git
array[waarnemingen-boten]=git@github.com:Amsterdam/waarnemingen-boten.git
array[kwiz-schuldhulpverlenings-monitor]=git@git.data.amsterdam.nl:Datapunt/kwiz-schuldhulpverlenings-monitor.git
array[tellus]=git@github.com:Amsterdam/tellus.git
array[blackspots]=git@github.com:Amsterdam/blackspots-backend.git

for i in "${!array[@]}"
do
    echo "key  : $i"
    echo "value: ${array[$i]}"
    git clone ${array[$i]} $i
    pushd $i
    git fetch 
    git co -B $BRANCH
    git reset --hard origin/master
    make upgrade
    make build
    make test
    git add requirements.txt requirements_dev.txt
    git commit -m "Maintenance run"
    popd
done

for i in "${!array[@]}"
do
    echo "key  : $i"
    echo "value: ${array[$i]}"
    pushd $i
    git push --set-upstream origin $BRANCH
    popd
done
