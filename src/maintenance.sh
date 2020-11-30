set -e 
DATE=$(date +"%y-%m-%d")
BRANCH=feature/maintenance-$DATE
echo "$BRANCH"
WORKDIR=workdir

declare -A array
array[bed-and-breakfast]=git@git.data.amsterdam.nl:Datapunt/bed-and-breakfast.git
array[iiif-metadata-server]=git@github.com:Amsterdam/iiif-metadata-server.git
array[iiif-auth-proxy]=git@github.com:Amsterdam/iiif-auth-proxy.git
array[waarnemingen-voertuigen]=git@github.com:Amsterdam/waarnemingen-voertuigen.git
array[waarnemingen-dashboard]=git@github.com:Amsterdam/waarnemingen-dashboard.git
array[waarnemingen-mensen]=git@github.com:Amsterdam/waarnemingen-mensen.git
array[waarnemingen-boten]=git@github.com:Amsterdam/waarnemingen-boten.git
array[kwiz-schuldhulpverlenings-monitor]=git@git.data.amsterdam.nl:Datapunt/kwiz-schuldhulpverlenings-monitor.git
array[tellus]=git@github.com:Amsterdam/tellus.git
array[blackspots]=git@github.com:Amsterdam/blackspots-backend.git

rm -rf $WORKDIR
mkdir $WORKDIR
pushd $WORKDIR
for i in "${!array[@]}"
do
    echo "key  : $i"
    echo "value: ${array[$i]}"
    git clone ${array[$i]} $i
    pushd $i
    git fetch 
    git co -B $BRANCH
    git reset --hard origin/master
    make requirements
    make build
    docker-compose down -v
    make test
    git add requirements.txt requirements_dev.txt
    git commit -m "Maintenance run ${date}"
    popd
done
popd

rm -f prlist.txt
for i in "${!array[@]}"
do
    pushd $i
    gh pr create --fill
    for num in `gh pr list -R ${array[$i]} --limit 999 2>/dev/null | awk '{print $1}'`; do
        gh pr view -R ${array[$i]} $num 2>/dev/null >> prlist.txt;
    done
    popd
done

cat prlist.txt | egrep -iv 'labels|assignees|reviewers|projects|milestone|number|state|^$'
