#!/bin/bash

# Created: 2024.09.13
# Vladimir Vons, VladVons@gmail.com
#

source ./common.sh


cProject="py-vMonit"
cUser="VladVons"
cMail="vladvons@gmail.com"
cUrl="https://github.com/${cUser}/${cProject}.git"
cBranch="main"


Clean()
{
  Log "$0->$FUNCNAME($*)"

  echo "delete objects"
  find . -name '*.pyc' -exec rm -v -f -R {} \;
  find . -name '*.log' -exec rm -v -f -R {} \;
  find . -name '__pycache__' -exec rm -v -f -R {} \;

  echo
  echo "Statistics *.py"
  #find . -name '*.py' -ls | awk '{total += $7} END {print total}'
  find ./src -name '*.py' | xargs wc
  find ./src -name '*.py' | wc -l
}


GitAuth()
{
  Log "$0->$FUNCNAME($*)"

  echo "It is not GIT password but SUDO "
  sudo chown -R $USER .

  # sign with eMail
  git config --global user.email "$cMail"
  git config --global user.name "$cUser"

  # token
  git config --global credential.helper libsecret
  git config --global credential.helper store

  git config -l
}


GitCreate()
{
  Log "$0->$FUNCNAME($*)"

  # create new project on disk
  git init
  GitAuth

  # remote git server location
  git remote add origin $cUrl

}


GitClone()
{
  Log "$0->$FUNCNAME($*)"

  # restore clone copy fromserver to disk 
  git clone --single-branch -b $Branch $Url
  GitAuth
}


GitReset()
{
  Log "$0->$FUNCNAME($*)"

  git checkout --orphan TEMP_BRANCH
  git add -A
  git commit -am "Initial commit"
  git branch -D $cBranch
  git branch -m $cBranch
  git push -f origin $cBranch
}


GitSyncToServ()
# sync only changes from disk to server 
{
  aComment="$1";
  Log "$0->$FUNCNAME($*)"

  git status

  #git add install.sh
  #git rm TestClient.py
  #git mv README.md README
  #git log

  git add -u -v
  git commit -a -m "$aComment"

  git push -u origin $cBranch 
  #ExecM "git push $cUrl -u origin $cBranch"
}


GitFromServ()
# sync changes from server to disk
{
  Log "$0->$FUNCNAME($*)"

  git pull
}


GitFromServF()
# sync changes from server to disk force
{
  Log "$0->$FUNCNAME($*)"

  git reset --hard origin/$cBranch
  git fetch --all
}



GitToServ()
# sync changes from disk to serv
{
  local aComment=${1:-"MyCommit"};
  Log "$0->$FUNCNAME($*)"

  #Clean
  # add all new files
  git add -A -v
  GitSyncToServ "$aComment"
}

GitNewBranch()
{
  NewBranch="master2"

  git checkout -b $NewBranch
  git add .
  git commit -m "from scratch"
  git push origin $NewBranch

  git remote set-head origin $NewBranch
  git config --global init.defaultBranch $NewBranch
  git symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/$NewBranch
  cat .git/refs/remotes/origin/HEAD
}


clear
case $1 in
    Clean)              "$1"        "$2" "$3" ;;
    GitAuth)            "$1"        "$2" "$3" ;;
    GitCreate)          "$1"        "$2" "$3" ;;
    GitToServ|t)        GitToServ   "$2" "$3" ;;
    GitFromServ|f)      GitFromServ "$2" "$3" ;;
    GitFromServF|ff)    GitFromServF "$2" "$3" ;;
    GitClone)           "$1"        "$2" "$3" ;;
esac
